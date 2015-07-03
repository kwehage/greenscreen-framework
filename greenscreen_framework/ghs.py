#!/usr/bin/env python3

import time
import string
import xlrd
import json
import os

'''
greenscreen_framework.py

This program consists of a collection of tools for importing data from
GreenScreen databases, translating data to GreenScreen format and performing
GreenScreen benchmark assessment. The present Python program can be executed
directly, or any of the various modules can be used from within another
Python program. Refer to the main() function at the end of the code for
example usage.

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


class InvalidGHSJapanFile_Error(Exception):
    pass


class GHSJapanData(object):
    '''
    description
    '''
    def __init__(self, sheet=None, filename=None):
        '''
        GHSJapanData Class constructor
        '''
        self.translation_criteria = {}
        self.translation_criteria['hazards'] = {
            'AA': {'name': 'Acute Aquatic Toxicity',
                   'list_members': []},
            'AT': {'name': 'Acute Mammalian Toxicity',
                   'list_members': []]},
            'C': {'name': 'Carcinogenicity',
                  'group': 'Group I Human'},
            'CA': {'name': 'Chronic Aquatic Toxicity',
                   'group': 'Ecotoxicity'},
            'D': {'name': 'Developmental Hazard',
                  'group': 'Group I Human'},
            'F': {'name': 'Flammability',
                  'group': 'Physical'},
            'IrE': {'name': 'Eye Irritation',
                    'group': 'Group II and II*'},
            'M': {'name': 'Mutagenicity',
                  'group': 'Group I'},
            'N_r': {'name': 'Neurotoxicity, Repeat Exposure',
                    'group': 'Group II and II*'},
            'N_s': {'name': 'Neurotoxicity, Single Exposure',
                    'group': 'Group II and II*'},
            'R': {'name': 'Reproductive',
                  'group': 'Group I'},
            'Rx': {'name': 'Reactivity',
                   'group': 'Physical'},
            'ST_r': {'name': 'Systemic Toxicity, Repeat Exposure',
                     'group': 'Group II and II*'},
            'ST_s': {'name': 'Systemic Toxicity, Single Exposure',
                     'group': 'Group II and II*'},
            'SnR': {'name': 'Sensitization, Respiratory',
                    'group': 'Group II and II*'},
            'SnS': {'name': 'Sensitization, Skin',
                    'group': 'Group II and II*'},
            'E': {'name': 'Endocrine Activity',
                  'group': 'Group I'},
            'P': {'name': 'Persistence',
                  'group': 'Fate'},
            'B': {'name': 'Bioaccumulation',
                  'group': 'Fate'},
            'IrS': {'name': 'Skin Irritation',
                    'group': 'Group II and II*'}}

        self.translation_criteria['lookup']['1'] = {}
        self.translation_criteria['lookup']['1']['Category 1A'] = 4
        self.translation_criteria['lookup']['1']['Category 1B'] = 4
        self.translation_criteria['lookup']['1']['Category 2'] = 3
        self.translation_criteria['lookup']['1']['Not classified'] = 2

        self.translation_criteria['lookup']['2'] = {}
        self.translation_criteria['lookup']['2']['Category 1'] = 5
        self.translation_criteria['lookup']['2']['Category 2'] = 5
        self.translation_criteria['lookup']['2']['Category 3'] = 4
        self.translation_criteria['lookup']['2']['Category 4'] = 3
        self.translation_criteria['lookup']['2']['Category 5'] = 2
        self.translation_criteria['lookup']['2']['Not classified'] = 2

        self.translation_criteria['lookup']['3'] = {}
        self.translation_criteria['lookup']['3']['Category 1'] = 5
        self.translation_criteria['lookup']['3']['Category 2'] = 4
        self.translation_criteria['lookup']['3']['Category 3'] = 3
        self.translation_criteria['lookup']['3']['Not classified'] = 2

        self.translation_criteria['lookup']['4'] = {}
        self.translation_criteria['lookup']['4']['Category 1'] = 4
        self.translation_criteria['lookup']['4']['Category 2'] = 3
        self.translation_criteria['lookup']['4']['Not classified'] = 2

        self.translation_criteria['lookup']['5'] = {}
        self.translation_criteria['lookup']['5']['Category 1A'] = 4
        self.translation_criteria['lookup']['5']['Category 1B'] = 3
        self.translation_criteria['lookup']['5']['Not classified'] = 2
        self.translation_criteria['lookup']['5']['Category1'] = 4

        self.translation_criteria['lookup']['6'] = {}
        self.translation_criteria['lookup']['6']['Category 1'] = 5
        self.translation_criteria['lookup']['6']['Category 2A'] = 4
        self.translation_criteria['lookup']['6']['Category 2B'] = 3
        self.translation_criteria['lookup']['6']['Not classified'] = 2

        self.translation_criteria['lookup']['7'] = {}
        self.translation_criteria['lookup']['7']['Category 4'] = 3

        self.translation_criteria['lookup']['8'] = {}
        self.translation_criteria['lookup']['8']['Not classified'] = 2

        self.translation_criteria['lookup']['9'] = {}
        self.translation_criteria['lookup']['9']['Category 1'] = 3
        self.translation_criteria['lookup']['9']['Not classified'] = 2

        self.translation_criteria['lookup']['10'] = {}
        self.translation_criteria['lookup']['10']['Category 1'] = 5
        self.translation_criteria['lookup']['10']['Category 2'] = 4
        self.translation_criteria['lookup']['10']['Category 3'] = 3
        self.translation_criteria['lookup']['10']['Category 4'] = 3
        self.translation_criteria['lookup']['10']['Not classified'] = 2

        self.translation_criteria['lookup']['11'] = {}
        self.translation_criteria['lookup']['11']['Category 1'] = 4
        self.translation_criteria['lookup']['11']['Not classified'] = 2

        self.translation_criteria['lookup']['12'] = {}
        self.translation_criteria['lookup']['12']['Category 1'] = 4
        self.translation_criteria['lookup']['12']['Category 2'] = 3
        self.translation_criteria['lookup']['12']['Category A'] = 3
        self.translation_criteria['lookup']['12']['Category B'] = 2
        self.translation_criteria['lookup']['12']['Not classified'] = 2

        self.translation_criteria['lookup']['13'] = {}
        self.translation_criteria['lookup']['13']['Category 1'] = 4
        self.translation_criteria['lookup']['13']['Category 2'] = 3
        self.translation_criteria['lookup']['13']['Category 3'] = 2
        self.translation_criteria['lookup']['13']['Not classified'] = 2

        if filename is None and sheet:
            absolute_fields = {'cas_number': [3, 'C'],
                               'descriptive_name': [4, 'C'],
                               'date_classified': [3, 'H'],
                               'ID': [3, 'C']}

            calculated_fields = {'date_imported': time.ctime(),
                                 'country': 'Japan'}

            self.data = {}
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

        elif filename:
            with open(filename, "r") as f:
                self.data = json.load(f)
            self.cas_number = self.data['cas_number']

        else:
            raise(InvalidGHSJapanFile_Error)

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

    def save(self, filepath):
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        with open(os.path.join(filepath, self.data['ID'] + ".json"), "w") as f:
            json.dump(self.data, f, indent=4, sort_keys=True)

if __name__ == "__main__":
    sheet = xlrd.open_workbook(
        'greenscreen_framework/data/h25_mhlw_new_e.xls').sheet_by_index(1)
    ghs_japan_data = GHSJapanData(sheet=sheet)
    ghs_japan_data.save("greenscreen_framework/data/ghs_json_data")
