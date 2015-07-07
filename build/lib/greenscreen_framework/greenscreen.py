#!/usr/bin/env python3

import sys
import os.path
import time
import getpass
import json
import re
import greenscreen_framework.ghs as ghs
if sys.version_info > (3,):
    from urllib.request import urlopen
else:
    import urllib2.urlopen as urlopen


'''
greenscreen_framework.py

This program consists of a collection of tools for translating hazard data to
GreenScreen format and performing GreenScreen benchmark assessment. The
present Python program can be executed directly, or any of the various modules
can be used from within another Python program. Refer to the main() function at
the end of the code for example usage.

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


class InvalidCAS_Error(Exception):
    pass


class MultipleSource_Error(Exception):
    pass


class GreenScreenData(object):
    def __init__(self, filename=None):
        if filename:
            with open(filename, "r") as f:
                self.data = json.load(f)
            self.cas_number = self.data['cas_number']
        else:
            self.cas_number = None
            self.data = {}
            self.data['cas_number'] = None
            self.data['cas_number_is_valid'] = None
            self.data['benchmark'] = None
            self.data['warning'] = []
            self.data['descriptive_name'] = []
            self.data['ID'] = None
            self.data['hazards'] = {
                'AA': {'name': 'Acute Aquatic Toxicity',
                       'group': 'Ecotoxicity'},
                'AT': {'name': 'Acute Mammalian Toxicity',
                       'group': 'Group II and II*'},
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

            for key, value in self.data['hazards'].items():
                value['date_imported'] = []
                value['imported_by'] = []
                value['source'] = []
                value['list_type'] = []
                value['list_rating'] = []
                value['hazard_rating'] = []
                value['date_classified'] = []
                value['overall_hazard_rating'] = 0

    def import_data(self, data, source=None):
        '''
        This function imports/translates data from GHSJapanData object into a
        GreenScreenData object.
        '''
        if source == 'GHS Japan':
            # GHS Japan has some entries with empty CAS numbers, ignore these
            if data.cas_number is "":
                print("Empty CAS number with ID: %s",
                      data.data['ID'])

            # validate cas number
            if len(data.cas_number[0]) > 0:
                validated = all([self.validate_cas(cas)
                                 for cas in data.cas_number])
            else:
                validated = False
            if validated:
                self.data['cas_number_is_valid'] = True
            else:
                self.data['warning'].append(
                    'Entry contains an invalid CAS number.')
                self.data['cas_number_is_valid'] = False

            self.data['cas_number'] = data.data['cas_number']
            self.data['descriptive_name'].append(
                data.data['descriptive_name'])
            if not self.data['ID']:
                self.data['ID'] = data.data['ID']

            for hazard, rating in data.data['translated_data'].items():
                if rating > 0:
                    self.data['hazards'][hazard]['date_imported'].append(
                        data.data['date_imported'])
                    self.data['hazards'][hazard]['imported_by'].append(
                        getpass.getuser())
                    self.data['hazards'][hazard]['source'].append(
                        data.data['source'])
                    self.data['hazards'][hazard]['list_type'].append(
                        data.data['list_type'])
                    self.data['hazards'][hazard]['list_rating'].append(
                        data.data['list_rating'])
                    self.data['hazards'][hazard]['hazard_rating'].append(
                        rating)
                    self.data['hazards'][hazard]['date_classified'].append(
                        data.data['date_classified'])
        self.trumping()
        self.benchmark()

    def validate_cas(self, cas):
        '''
        CAS Validation has two steps:
        Step 1: Verify that the number is formatted correctly (2-7 digits)-
                (1-2 digits)-(1 check sum digit)
        Step 2: Verify that the check sum is the correct amount when compared
                to the remainder of the rest of the numbers combined and
                multiplied according to the CAS validation system
        '''
        ## Regular Expression used to validate number format
        m_obj = re.match(r"(\d{2,7}-\d{1,2}-\d$)", cas)
        m_obj.group(0)

        new_cas = cas.replace("-", "")
        check_cas = cas[-1]
        new_cas = new_cas[:-1]
        new_cas = new_cas[::-1]
        total_valid_value = 0
        for x in range(0, len(new_cas)):
            valid_value = int(new_cas[x]) * (x + 1)
            total_valid_value += valid_value
        if total_valid_value % (10) == int(check_cas):
            pass
        else:
            print("Invalid CAS: " + cas)
            return False
        return True

    def benchmark(self):
        '''
        Perform GreenScreen benchmarking
        '''

        AA = self.data['hazards']['AA']['overall_hazard_rating']
        AT = self.data['hazards']['AT']['overall_hazard_rating']
        C = self.data['hazards']['C']['overall_hazard_rating']
        CA = self.data['hazards']['CA']['overall_hazard_rating']
        D = self.data['hazards']['D']['overall_hazard_rating']
        R = self.data['hazards']['R']['overall_hazard_rating']
        F = self.data['hazards']['F']['overall_hazard_rating']
        IrE = self.data['hazards']['IrE']['overall_hazard_rating']
        IrS = self.data['hazards']['IrS']['overall_hazard_rating']
        M = self.data['hazards']['M']['overall_hazard_rating']
        N_s = self.data['hazards']['N_s']['overall_hazard_rating']
        N_r = self.data['hazards']['N_r']['overall_hazard_rating']
        Rx = self.data['hazards']['Rx']['overall_hazard_rating']
        ST_s = self.data['hazards']['ST_s']['overall_hazard_rating']
        ST_r = self.data['hazards']['ST_r']['overall_hazard_rating']
        SnR = self.data['hazards']['SnR']['overall_hazard_rating']
        SnS = self.data['hazards']['SnS']['overall_hazard_rating']
        E = self.data['hazards']['E']['overall_hazard_rating']
        P = self.data['hazards']['P']['overall_hazard_rating']
        B = self.data['hazards']['B']['overall_hazard_rating']

        ## Neurotoxicity
        N = max([N_r, N_s])

        ## Toxicity
        T = max([AT, ST_r, ST_s])

        ## Eco Toxicity
        eco_T = max([CA, AA])
        vHigh_T_B1 = max([T, eco_T])
        Group_1 = max([C, M, D, N, E])
        Group_2 = max([AT, ST_s, N_s, IrE, IrS])
        Group_2_star = max([ST_r, N_r, SnR, SnS])
        all_four_groups = max([eco_T, Group_1, Group_2, Group_2_star])

        ## Benchmark 1
        if (((P >= 4) and (B >= 4) and
            ((max([eco_T, Group_2]) >= 5) or
             (max([Group_1, Group_2_star]) >= 4))) or
                # High P, B, (vHigh T or High T)
            ((P >= 5) and (B >= 5)) or
                # vHigh P, vHigh B
            ((P >= 5) and ((max([eco_T, Group_2]) >= 5) or
             (max([Group_1, Group_2_star]) >= 4))) or
                # vHigh P, (vHigh T or High T)
            ((B >= 5) and ((max([eco_T, Group_2]) >= 5) or
             (max([Group_1, Group_2_star]) >= 4))) or
                # vHigh B, (vHigh T or High T)
                (Group_1 >= 4)):  # Group I Human
            self.data['benchmark'] = 'Benchmark 1'

        ## Benchmark 2
        elif (((P >= 3) and (B >= 3) and (all_four_groups >= 3)) or
                # Moderate P, B, T
              ((P >= 4) and (B >= 4)) or
                # High P, High B
              ((P >= 4) and (all_four_groups >= 3)) or
                # High B, Moderate T
              ((B >= 4) and (all_four_groups >= 3)) or
                # High B, Moderate T
              (Group_1 >= 3) or
                # moderate Moderate T (Group I Human)
              ((max([eco_T, Group_2]) >= 5) or (Group_2_star >= 4)) or
                # vHigh T (Eco_T or Group II) or High T (Group_2_star)
              (F >= 4) or  # High F
                (Rx >= 4)):  # High Rx
            self.data['benchmark'] = 'Benchmark 2'

        ## Benchmark 3
        elif ((P >= 3) or  # moderate P
              (B >= 3) or  # moderate B
              (eco_T >= 3) or  # moderate eco_T
              (max([Group_2, Group_2_star]) >= 3) or  # moderate T
              (F >= 3) or  # moderate F
                (Rx >= 3)):  # moderate Rx
            self.data['benchmark'] = 'Benchmark 3'

        ## Benchmark 4
        elif ((P <= 2) and  # low P
              (B <= 2) and  # low B
              (all_four_groups <= 2) and  # low four_groups
              (F <= 2) and
              (Rx <= 2) and
              (B != 0) and
              (T != 0) and
                (eco_T != 0)):  # moderate T
            self.data['benchmark'] = 'Benchmark 4'

        else:
            self.data['benchmark'] = 'Benchmark U'

    def trumping(self):
        for hazard in self.data['hazards'].values():
            for list_rating in range(4, 0, -1):
                rating = \
                    [i for i, j in zip(
                        hazard['hazard_rating'],
                        hazard['list_rating']) if j is list_rating]
                if rating:
                    rating = max(rating)
                    break
            if rating:
                hazard['overall_hazard_rating'] = rating
            else:
                hazard['overall_hazard_rating'] = 0

    def save(self, data_dir):
        data_dir_split = data_dir.split('/')
        cwd = os.getcwd()
        if data_dir_split[0] == '':
            os.chdir('/')
        for element in data_dir_split:
            if not element == '':
                if not os.path.exists(element):
                    os.makedirs(element)
                os.chdir(element)
        os.chdir(cwd)

        if len(self.data['ID']) > 0:
            with open(
                    os.path.join(data_dir, self.data['ID'] + '.json'),
                    'w') as f:
                json.dump(self.data, f, indent=4, sort_keys=True)


def bulk_ghs_japan_import(ghs_japan_file_path, greenscreen_file_path):
    greenscreen_data = {}
    for ghs_japan_file in os.listdir(ghs_japan_file_path):
        ghs_japan_data = ghs.GHSJapanData(
            filename=os.path.join(ghs_japan_file_path, ghs_japan_file))
        if ghs_japan_data.data['ID'] not in greenscreen_data:
            greenscreen_data[ghs_japan_data.data['ID']] = GreenScreenData()
        greenscreen_data[ghs_japan_data.data['ID']].import_data(
            ghs_japan_data, source='GHS Japan')
    for ID, item in greenscreen_data.items():
        item.save(greenscreen_file_path)
    # compute basic statistics
    benchmark_counts = [item.data['benchmark'] for
                        item in greenscreen_data.values()]
    print('Benchmark 1: %d' % benchmark_counts.count('Benchmark 1'))
    print('Benchmark 2: %d' % benchmark_counts.count('Benchmark 2'))
    print('Benchmark 3: %d' % benchmark_counts.count('Benchmark 3'))
    print('Benchmark 4: %d' % benchmark_counts.count('Benchmark 4'))
    print('Benchmark U: %d' % benchmark_counts.count('Benchmark U'))


if __name__ == "__main__":
    t = time.time()
    greenscreen_file_path = 'data/greenscreen_data'
    ghs_japan_file_path = 'data/ghs_json_data'
    bulk_ghs_japan_import(ghs_japan_file_path, greenscreen_file_path)
    print('Time elapsed: %d seconds' % (time.time() - t))
