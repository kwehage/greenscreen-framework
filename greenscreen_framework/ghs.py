#!/usr/bin/env python3

import time
import string
import xlrd
import json
import os
import re
import sys
from urllib.request import urlopen

'''
ghs.py

This module contains a Python class, 'GHSJapanData', that is used
to import data from the GHS Japan website and translate the hazards from
their native representation to GreenScreen hazard specification.

Copyright 2013-2015 Kristopher Wehage
University of California-Davis

THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.
'''

__author__ = '''Kristopher Wehage (ktwehage@ucdavis.edu)'''

regex = re.compile(r"[A-Za-z][A-Za-z1-9 ]*?\(.*?\)")


class InvalidGHSJapanFile_Error(Exception):
    pass


class GHSJapanData(object):
    '''
    GHSJapanData Constructor
    '''
    def __init__(self, sheet=None, filename=None, file_path=None):
        '''
        GHSJapanData Class constructor
        '''
        self.data = {'file_path': file_path}
        self.systemic_keywords = [
            'respiratory', 'blood', 'kidney', 'liver',
            'adrenal', 'gastro', 'systemic', 'eye', 'heart',
            'bone', 'hematop', 'cardio', 'spleen', 'thyroid',
            'lung', 'gingi', 'testes', 'urinary']

        self.neuro_keywords = ['neuro', 'nervous']

        self.translation_patterns = {
            '1': {
                'Category 1A': 4,
                'Category 1B': 4,
                'Category 2': 3,
                'Not classified': 2},
            '2': {
                'Category 1': 5,
                'Category 2': 5,
                'Category 3': 4,
                'Category 4': 3,
                'Category 5': 2,
                'Not classified': 2},
            '3': {
                'Category 1': 5,
                'Category 2': 4,
                'Category 3': 3,
                'Not classified': 2},
            '4': {
                'Category 1': 4,
                'Category 2': 3,
                'Not classified': 2},
            '5': {
                'Category 1A': 4,
                'Category 1B': 3,
                'Not classified': 2,
                'Category1': 4},
            '6': {
                'Category 1': 5,
                'Category 2A': 4,
                'Category 2B': 3,
                'Not classified': 2},
            '7': {
                'Category 4': 3},
            '8': {
                'Not classified': 2},
            '9': {
                'Category 1': 3,
                'Not classified': 2},
            '10': {
                'Category 1': 5,
                'Category 2': 4,
                'Category 3': 3,
                'Category 4': 3,
                'Not classified': 2},
            '11': {
                'Category 1': 4,
                'Not classified': 2},
            '12': {
                'Category 1': 4,
                'Category 2': 3,
                'Category A': 3,
                'Category B': 2,
                'Not classified': 2},
            '13': {
                'Category 1': 4,
                'Category 2': 3,
                'Category 3': 2,
                'Not classified': 2}}

        self.translation_criteria = {
            'AA': {'name': 'Acute Aquatic Toxicity',
                   'native_classification': [
                       'acute_aquatic_toxicity'],
                   'pattern': [self.translation_patterns['3']],
                   'requires_parsing': False},

            'AT': {'name': 'Acute Mammalian Toxicity',
                   'native_classification': [
                       'acute_toxicity_oral',
                       'acute_toxicity_dermal',
                       'acute_toxicity_inhalation_gas',
                       'acute_toxicity_inhalation_vapor',
                       'acute_toxicity_inhalation_dust'],
                   'pattern': [self.translation_patterns['2']] * 5,
                   'requires_parsing': False},

            'C': {'name': 'Carcinogenicity',
                  'native_classification': [
                      'carcinogenicity'],
                  'pattern': [self.translation_patterns['1']],
                  'requires_parsing': False},

            'CA': {'name': 'Chronic Aquatic Toxicity',
                   'native_classification': [
                       'chronic_aquatic_toxicity'],
                   'pattern': [self.translation_patterns['7']],
                   'requires_parsing': False},

            'F': {'name': 'Flammability',
                  'native_classification': [
                      'flammable_gases',
                      'flammable_aerosols',
                      'flammable_liquids',
                      'flammable_solids'],
                  'pattern': [
                      self.translation_patterns['12'],
                      self.translation_patterns['13'],
                      self.translation_patterns['10'],
                      self.translation_patterns['4']],
                  'requires_parsing': False},

            'M': {'name': 'Mutagenicity',
                  'native_classification': [
                      'germ_cell_mutagenicity'],
                  'pattern': [self.translation_patterns['1']],
                  'requires_parsing': False},

            'D': {'name': 'Developmental Hazard',
                  'native_classification': [
                      'reproductive_toxicity'],
                  'pattern': [self.translation_patterns['1']],
                  'requires_parsing': False},

            'R': {'name': 'Reproductive',
                  'native_classification': [
                      'reproductive_toxicity'],
                  'pattern': [self.translation_patterns['1']],
                  'requires_parsing': False},

            'Rx': {'name': 'Reactivity',
                   'native_classification': [
                       'explosives',
                       'self_reactive_substances',
                       'substances_mixtures_emit_flammable' +
                       '_gas_in_contact_with_water',
                       'oxidizing_gases',
                       'oxidizing_solids',
                       'organic_peroxides',
                       'self_heating_substances',
                       'corrosive_to_metals'],
                   'pattern': [
                       self.translation_patterns['8'],
                       self.translation_patterns['8'],
                       self.translation_patterns['3'],
                       self.translation_patterns['11'],
                       self.translation_patterns['3'],
                       self.translation_patterns['3'],
                       self.translation_patterns['8'],
                       self.translation_patterns['4'],
                       self.translation_patterns['9']],
                   'requires_parsing': False},

            'SnR': {'name': 'Sensitization, Respiratory',
                    'native_classification': [
                        'respiratory_sensitizer'],
                    'pattern': [self.translation_patterns['5']],
                    'requires_parsing': False},

            'SnS': {'name': 'Sensitization, Skin',
                    'native_classification': [
                        'skin_sensitizer'],
                    'pattern': [self.translation_patterns['5']],
                    'requires_parsing': False},

            'E': {'name': 'Endocrine Activity',
                  'native_classification': [],
                  'pattern': [],
                  'requires_parsing': False},

            'P': {'name': 'Persistence',
                  'native_classification': [],
                  'pattern': [],
                  'requires_parsing': False},

            'B': {'name': 'Bioaccumulation',
                  'native_classification': [],
                  'pattern': [],
                  'requires_parsing': False},

            'IrS': {'name': 'Skin Irritation',
                    'native_classification': [
                        'skin_corrosion_irritation'],
                    'pattern': [self.translation_patterns['3']],
                    'requires_parsing': False},

            'IrE': {'name': 'Eye Irritation',
                    'native_classification': [
                        'serious_eye_damage_irritation'],
                    'pattern': [self.translation_patterns['6']],
                    'requires_parsing': False},

            # In the following four cases, multiple greenscreen hazards
            # are stored under a single ghs japan hazard. A regular expression
            # is provided that uniquely identifies each hazard group.
            # The hazard is only assigned to the greenscreen hazard if
            # one of the provided keywords is found in the grouping

            # Neurotoxicity / systemic toxicity, repeat exposure
            # are grouped together under 'systemic_toxicity_repeat_exposure'
            'N_r': {'name': 'Neurotoxicity, Repeat Exposure',
                    'native_classification': [
                        'systemic_toxicity_repeat_exposure'],
                    'pattern': [self.translation_patterns['4']],
                    'requires_parsing': True,
                    'regex': regex,
                    'keywords': self.neuro_keywords},

            'ST_r': {'name': 'Systemic Toxicity, Repeat Exposure',
                     'native_classification': [
                         'systemic_toxicity_repeat_exposure'],
                     'pattern': [self.translation_patterns['3']],
                     'requires_parsing': True,
                     'regex': regex,
                     'keywords': self.systemic_keywords},

            # Neurotoxicity / systemic toxicity, single exposure
            # are grouped together under 'systemic_toxicity_single_exposure'
            'N_s': {'name': 'Neurotoxicity, Single Exposure',
                    'native_classification': [
                        'systemic_toxicity_single_exposure'],
                    'pattern': [self.translation_patterns['4']],
                    'requires_parsing': True,
                    'regex': regex,
                    'keywords': self.neuro_keywords},

            'ST_s': {'name': 'Systemic Toxicity, Single Exposure',
                     'native_classification': [
                         'systemic_toxicity_single_exposure'],
                     'pattern': [self.translation_patterns['3']],
                     'requires_parsing': True,
                     'regex': regex,
                     'keywords': self.systemic_keywords}}

        if filename is None and sheet:
            self.import_data(sheet)
            self.translate()

        elif filename:
            with open(filename, "r") as f:
                self.data = json.load(f)
            self.cas_number = self.data['cas_number']

        else:
            raise(InvalidGHSJapanFile_Error)

    def import_data(self, sheet):
        absolute_fields = {'cas_number': [3, 'C'],
                           'descriptive_name': [4, 'C'],
                           'date_classified': [3, 'H'],
                           'ID': [3, 'C']}

        calculated_fields = {'date_imported': time.ctime(),
                             'country': 'Japan'}

        self.data['list_type'] = 'Screening A'
        self.data['list_rating'] = 2
        self.data['source'] = 'GHS Japan Country List'
        for key in absolute_fields:
            self.data[key] = \
                sheet.cell_value(
                    absolute_fields[key][0] - 1,
                    self.excel_col_to_num(absolute_fields[key][1]))

        self.data['date_classified'] = self.data['date_classified'][2:]
        self.data['cas_number'] = \
            self.data['cas_number'].replace(' ', '').split(',')

        self.cas_number = self.data['cas_number']

        for key, val in calculated_fields.items():
            self.data[key] = val

        hazards = {}
        hazards['ghs_physical_hazards'] = \
            ['explosives',
             'flammable_gases',
             'flammable_aerosols',
             'oxidizing_gases',
             'gases_under_pressure',
             'flammable_liquids',
             'flammable_solids',
             'self_reactive_substances',
             'pyrophoric_liquids',
             'pyrophoric_solids',
             'self_heating_substances',
             'substances_mixtures_emit_flammable' +
             '_gas_in_contact_with_water',
             'oxidizing_liquids',
             'oxidizing_solids',
             'organic_peroxides',
             'corrosive_to_metals']

        hazards['ghs_health_hazards'] = \
            ['acute_toxicity_oral',
             'acute_toxicity_dermal',
             'acute_toxicity_inhalation_gas',
             'acute_toxicity_inhalation_vapor',
             'acute_toxicity_inhalation_dust',
             'skin_corrosion_irritation',
             'serious_eye_damage_irritation',
             'respiratory_sensitizer',
             'skin_sensitizer',
             'germ_cell_mutagenicity',
             'carcinogenicity',
             'reproductive_toxicity',
             'systemic_toxicity_single_exposure',
             'systemic_toxicity_repeat_exposure',
             'aspiration_hazard']

        hazards['ghs_environmental_hazards'] = \
            ['acute_aquatic_toxicity',
             'chronic_aquatic_toxicity',
             'hazardous_to_ozone']

        hazard_fields = {'hazard_name': 'C',
                         'hazard_id': 'B',
                         'classification': 'D',
                         'hazard_statement': 'G',
                         'rationale': 'H',
                         'signal_word': 'F',
                         'symbol': 'E'}

        row_ind = [range(8, 24), range(27, 42), range(45, 48)]

        self.data['hazards'] = {}
        for key, rows in zip(['ghs_physical_hazards',
                              'ghs_health_hazards',
                              'ghs_environmental_hazards'],
                             row_ind):
            for val, row in zip(hazards[key], rows):
                self.data['hazards'][val] = {}
                for hazard, col in hazard_fields.items():
                    try:
                        self.data['hazards'][val][hazard] = \
                            sheet.cell_value(
                                row - 1,
                                self.excel_col_to_num(col))
                        if type(self.data['hazards'][val][hazard]) is str:
                            # clean artefacts from text
                            for element in [u'\uff08',
                                            u'\xf6',
                                            u'\xba',
                                            u'\uff09']:
                                self.data['hazards'][val][hazard] = \
                                    self.data['hazards'][val][
                                        hazard].replace(element, u'')
                    except:
                        # print("Could not load data from cell: (%d %s)" %
                        #       (row, col))
                        pass

    def excel_col_to_num(self, column):
        '''utility to convert excel column indices to Python column
        indices'''
        sum_ = 0
        for l in column:
            if l not in string.ascii_letters:
                return False
            sum_ *= 26
            sum_ += ord(l.upper()) - 64
        return sum_ - 1

    def translate(self):
        self.data['translated_data'] = {}
        for key, value in self.translation_criteria.items():
            rating = []

            # if no parsing is required, the translation is a direct
            # conversion using the lookup patterns defined in
            # self.translation_patterns
            if not value['requires_parsing']:
                for native_hazard, pattern in \
                        zip(value['native_classification'],
                            value['pattern']):
                    for classification in pattern:
                        if classification in \
                                self.data['hazards'][native_hazard][
                                'classification']:
                            rating.append(pattern[classification])
                if rating:
                    self.data['translated_data'][key] = max(rating)
                else:
                    self.data['translated_data'][key] = 0

            # otherwise, if parsing is required, use the regular
            # expressions and keywords to identify hazard group and
            # hazard assignment.
            else:
                for native_hazard, pattern in \
                        zip(value['native_classification'],
                            value['pattern']):
                    for match in value['regex'].finditer(
                            self.data['hazards'][native_hazard][
                                'classification']):
                        if any(word in match.string for word in
                                value['keywords']):
                            [rating.append(pattern[classification]) for
                             classification in pattern if
                             classification in match.string]
                if rating:
                    self.data['translated_data'][key] = max(rating)
                else:
                    self.data['translated_data'][key] = 0

    def save(self, filepath):
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        filename = self.data['ID'] + '.json'
        if os.path.exists(os.path.join(filepath, self.data['ID'] + '.json')):
            i = 2
            while True:
                filename = self.data['ID'] + '_%s.json' % i
                i += 1
                if not os.path.exists(os.path.join(filepath, filename)):
                    break
        with open(os.path.join(filepath, filename), "w") as f:
            json.dump(self.data, f, indent=4, sort_keys=True)


def batch_process(
        excel_file_path,
        ghs_japan_file_path,
        url='http://www.safe.nite.go.jp/english/ghs/files/',
        file_list=['h25_mhlw_new_e.xls',
                   'h25_mhlw_rev_e.xls',
                   'h24_mhlw_new_e.xls',
                   'h24_mhlw_rev_e.xls',
                   'h23_mhlw_new_e.xls',
                   'h23_mhlw_rev_e.xls',
                   'h22_mhlw_new_e.xls',
                   'h22_mhlw_rev_e.xls',
                   'h21_mhlw_new_e.xls',
                   'h21_mhlw_rev_e.xls',
                   'h20_mhlw_new_e.xls',
                   'h20_mhlw_rev_e.xls',
                   'h20_meti_new_e.xls',
                   'h20_meti_rev_e.xls',
                   'h19_mhlw_danger_e.xls',
                   'h19_mhlw_hazard_e.xls',
                   'h19_meti_new_e.xls',
                   'h19_meti_rev_e.xls',
                   'h18_imcg_e.xls']):

    if not os.path.exists(excel_file_path):
        os.makedirs(excel_file_path)
    if not os.path.exists(ghs_japan_file_path):
        os.makedirs(ghs_japan_file_path)
    for file_name in file_list:
        full_path = os.path.join(excel_file_path, file_name)
        if not os.path.isfile(full_path):
            download_path = url + file_name
            u = urlopen(download_path)
            with open(full_path, 'wb') as f:
                meta = u.info()
                filesize = int(meta.get("Content-Length"))
                print("Downloading: %s Bytes: %s" % (full_path, filesize))
                filesize_dl = 0
                blocksize = 64 * 1024
                while True:
                    buff = u.read(blocksize)
                    if not buff:
                        break
                    filesize_dl += len(buff)
                    f.write(buff)
                    status = r"%10d [%3.2f%%]" % \
                        (filesize_dl, filesize_dl * 100 / filesize)
                    status = status + chr(8) * (len(status) + 1)
                    sys.stdout.write('\r')
                    sys.stdout.flush()
                    sys.stdout.write(status)
        book = xlrd.open_workbook(full_path)
        for i in range(1, book.nsheets):
            sheet = book.sheet_by_index(i)
            ghs_japan_data = GHSJapanData(sheet=sheet, file_path=file_name)
            ghs_japan_data.save(ghs_japan_file_path)

if __name__ == "__main__":
    t = time.time()
    excel_file_path = 'data'
    ghs_japan_file_path = 'data/ghs_json_data'
    batch_process(excel_file_path, ghs_japan_file_path)
    print('Time elapsed: %d seconds' % (time.time() - t))
