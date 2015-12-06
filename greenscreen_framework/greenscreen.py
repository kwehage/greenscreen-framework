#!/usr/bin/env python3

import os.path
import time
import getpass
import json
import re
import greenscreen_framework.ghs as ghs
import greenscreen_framework.prop65 as prop65


'''
greenscreen.py

This program consists of a collection of tools for translating hazard data to
GreenScreen format and performing GreenScreen benchmark assessment. This
Python program can be executed directly, or any of the various modules
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


class GreenScreenData(object):
    '''
    This Python class contains datastructures to store the
    results of hazard endpoint classification imported from multiple sources.
    Additionally, the class contains methods to perform an overall benchmark
    assessment based on the data that has been imported. If the assessment has
    not been verified by a GreenScreen licensed profiler, the benchmark score
    that is generated is considered as provisional, and a "List Translation"
    result is reported to the user.
    '''

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
            self.data['verified_by_greenscreen_profiler'] = False
            self.data['verified_by'] = None
            self.data['verified_date'] = None
            self.data['list_translation'] = None
            self.data['overall_list_rating'] = 0
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
                value['overall_list_rating'] = 0

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
        self.list_translation()

    def validate_cas(self, cas):
        '''
        CAS Validation has two steps:
        Step 1: Verify that the number is formatted correctly (2-7 digits)-
                (1-2 digits)-(1 check sum digit)
        Step 2: Verify that the check sum is the correct amount when compared
                to the remainder of the rest of the numbers combined and
                multiplied according to the CAS validation system
        '''
        # Regular Expression used to validate number format
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

    def max_group_rating(self, hazards, list_ratings):
        hazard = max(hazards)
        # find all occurrences of maximum score, there may be more than one
        list_indices = [i for i, x in enumerate(hazards) if x == hazard]
        list_rating = max([list_ratings[i] for i in list_indices])
        return hazard, list_rating

    def benchmark(self):
        '''
        Perform GreenScreen benchmarking
        '''
        AA = self.data['hazards']['AA']['overall_hazard_rating']
        AA_rating = self.data['hazards']['AA']['overall_list_rating']

        AT = self.data['hazards']['AT']['overall_hazard_rating']
        AT_rating = self.data['hazards']['AT']['overall_list_rating']

        C = self.data['hazards']['C']['overall_hazard_rating']
        C_rating = self.data['hazards']['C']['overall_list_rating']

        CA = self.data['hazards']['CA']['overall_hazard_rating']
        CA_rating = self.data['hazards']['CA']['overall_list_rating']

        D = self.data['hazards']['D']['overall_hazard_rating']
        D_rating = self.data['hazards']['D']['overall_list_rating']

        R = self.data['hazards']['R']['overall_hazard_rating']
        R_rating = self.data['hazards']['R']['overall_list_rating']

        F = self.data['hazards']['F']['overall_hazard_rating']
        F_rating = self.data['hazards']['F']['overall_list_rating']

        IrE = self.data['hazards']['IrE']['overall_hazard_rating']
        IrE_rating = self.data['hazards']['IrE']['overall_list_rating']

        IrS = self.data['hazards']['IrS']['overall_hazard_rating']
        IrS_rating = self.data['hazards']['IrS']['overall_list_rating']

        M = self.data['hazards']['M']['overall_hazard_rating']
        M_rating = self.data['hazards']['M']['overall_list_rating']

        N_s = self.data['hazards']['N_s']['overall_hazard_rating']
        N_s_rating = self.data['hazards']['N_s']['overall_list_rating']

        N_r = self.data['hazards']['N_r']['overall_hazard_rating']
        N_r_rating = self.data['hazards']['N_r']['overall_list_rating']

        Rx = self.data['hazards']['Rx']['overall_hazard_rating']
        Rx_rating = self.data['hazards']['Rx']['overall_list_rating']

        ST_s = self.data['hazards']['ST_s']['overall_hazard_rating']
        ST_s_rating = self.data['hazards']['ST_s']['overall_list_rating']

        ST_r = self.data['hazards']['ST_r']['overall_hazard_rating']
        ST_r_rating = self.data['hazards']['ST_r']['overall_list_rating']

        SnR = self.data['hazards']['SnR']['overall_hazard_rating']
        SnR_rating = self.data['hazards']['SnR']['overall_list_rating']

        SnS = self.data['hazards']['SnS']['overall_hazard_rating']
        SnS_rating = self.data['hazards']['SnS']['overall_list_rating']

        E = self.data['hazards']['E']['overall_hazard_rating']
        E_rating = self.data['hazards']['E']['overall_list_rating']

        P = self.data['hazards']['P']['overall_hazard_rating']
        P_rating = self.data['hazards']['P']['overall_list_rating']

        B = self.data['hazards']['B']['overall_hazard_rating']
        B_rating = self.data['hazards']['B']['overall_list_rating']

        # Neurotoxicity
        N, N_rating = self.max_group_rating(
            [N_r, N_s],
            [N_r_rating, N_s_rating])

        # Toxicity
        T, T_rating = self.max_group_rating(
            [AT, ST_r, ST_s],
            [AT_rating, ST_r_rating, ST_s_rating])

        # Eco Toxicity
        eco_T, eco_T_rating = self.max_group_rating(
            [CA, AA],
            [CA_rating, AA_rating])

        Group_1, Group_1_rating = self.max_group_rating(
            [C, M, D, N, E, R],
            [C_rating, M_rating, D_rating, N_rating, E_rating, R_rating])

        Group_2, Group_2_rating = self.max_group_rating(
            [AT, ST_s, N_s, IrE, IrS],
            [AT_rating, ST_s_rating, N_s_rating, IrE_rating, IrS_rating])

        Group_2_star, Group_2_star_rating = self.max_group_rating(
            [ST_r, N_r, SnR, SnS],
            [ST_r_rating, N_r_rating, SnR_rating, SnS_rating])

        all_four_groups, all_four_groups_rating = self.max_group_rating(
            [eco_T, Group_1, Group_2, Group_2_star],
            [eco_T_rating, Group_1_rating,
             Group_2_rating, Group_2_star_rating])

        # Benchmark 1
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

            # additional criteria for greenscreen 'list translator'
            # record list type that resulted in Benchmark 1
            # assessment
            overall_list_rating = []
            if P >= 4 and B >= 4 and max([eco_T, Group_2]) >= 5:
                if eco_T > Group_2:
                    temp_rating = eco_T_rating
                else:
                    temp_rating = Group_2_rating
                overall_list_rating.append(
                    min(P_rating, B_rating, temp_rating))
            if max([Group_1, Group_2_star]) >= 4:
                if Group_1 > Group_2_star:
                    overall_list_rating.append(Group_1_rating)
                else:
                    overall_list_rating.append(Group_2_star_rating)
            if P >= 5 and B >= 5:
                overall_list_rating.append(min(P_rating, B_rating))
            if P >= 5 and max([eco_T, Group_2]) >= 5:
                if eco_T > Group_2:
                    temp_rating = eco_T_rating
                else:
                    temp_rating = Group_2_rating
                overall_list_rating.append(min(P_rating, temp_rating))
            if max([Group_1, Group_2_star]) >= 4:
                if Group_1 > Group_2_star:
                    overall_list_rating.append(Group_1_rating)
                else:
                    overall_list_rating.append(Group_2_star_rating)
            if B >= 5 and max([eco_T, Group_2]) >= 5:
                if eco_T > Group_2:
                    temp_rating = eco_T_rating
                else:
                    temp_rating = Group_2_rating
                overall_list_rating.append(min(B_rating, temp_rating))
            if max([Group_1, Group_2_star]) >= 4:
                if Group_1 > Group_2_star:
                    overall_list_rating.append(Group_1_rating)
                else:
                    overall_list_rating.append(Group_2_star_rating)
            if Group_1 >= 4:
                overall_list_rating.append(Group_1_rating)
            self.data['overall_list_rating'] = max(overall_list_rating)

        # Benchmark 2
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

        # Benchmark 3
        elif ((P >= 3) or  # moderate P
              (B >= 3) or  # moderate B
              (eco_T >= 3) or  # moderate eco_T
              (max([Group_2, Group_2_star]) >= 3) or  # moderate T
              (F >= 3) or  # moderate F
                (Rx >= 3)):  # moderate Rx
            self.data['benchmark'] = 'Benchmark 3'

        # Benchmark 4
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
        '''
        The GreenScreen methodology provides guidance for weighting hazard
        data from multiple sources. Hazard data sources are classified as:

            4. Authoritative A
            3. Authoritative B
            2. Screening A
            1. Screening B

        The list rating is stored as the corresponding numerical value (1-4)
        within the Python datastructure. If multiple datasources are available,
        the overall hazard classification is based on the "Trumping Criteria"
        described in the GreenScreen methodology: Authoritative A results trump
        Authoritative B, which trump Screening A, which trump Screening B. This
        process translates to a Python "generator" programming construct.
        '''
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
                hazard['overall_list_rating'] = list_rating
            else:
                hazard['overall_hazard_rating'] = 0

    def list_translation(self):
        '''
        At this point, any benchmark score that has been generated may be
        considered as a "provisional" score. The benchmark score should not
        be reported as a GreenScreen benchmark until a GreenScreen licensed
        profiler has reviewed the data, appended additional information as
        necessary, and validated the result. If the data has not been validated
        by a GreenScreen professional, the result of assessment may be reported
        as a GreenScreen "List Translation" for Benchmark 1 chemicals. If the
        Benchmark 1 score is generated from an "Authoritative A" list, the
        score is reported as a "LT-1: Benchmark 1". If the Benchmark 1 score
        is generated from an Authoritative B, Screening A or Screening B list
        the score is reported as "LT-1: Possible Benchmark 1".
        '''

        if self.data['benchmark'] is 'Benchmark 1':
            if self.data['overall_list_rating'] is 4:
                self.data['list_translation'] = 'LT-1: Benchmark 1'
            else:
                self.data['list_translation'] = 'LT-P1: Possible Benchmark 1'
        else:
            self.data['list_translation'] = 'LT-U: Unspecified Benchmark'

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


def bulk_ghs_japan_import(
        ghs_japan_file_path,
        greenscreen_file_path,
        greenscreen_data={}):
    for ghs_japan_file in os.listdir(ghs_japan_file_path):
        ghs_japan_data = ghs.GHSJapanData(
            filename=os.path.join(ghs_japan_file_path, ghs_japan_file))
        if ghs_japan_data.data['ID'] not in greenscreen_data:
            greenscreen_data[ghs_japan_data.data['ID']] = GreenScreenData()
        greenscreen_data[ghs_japan_data.data['ID']].import_data(
            ghs_japan_data, source='GHS Japan')
    del greenscreen_data['']
    for ID, item in greenscreen_data.items():
        item.save(greenscreen_file_path)
    return greenscreen_data


def bulk_prop65_import(
        prop65_file_path,
        greenscreen_file_path,
        greenscreen_data={}):
    for prop65_file in os.listdir(prop65_file_path):
        prop65_data = prop65.Prop65Data(
            filename=os.path.join(prop65_file_path, prop65_file))
        if prop65_data.data['ID'] not in greenscreen_data:
            greenscreen_data[prop65_data.data['ID']] = GreenScreenData()
        greenscreen_data[prop65_data.data['ID']].import_data(
            prop65_data, source='Proposition 65')
    del greenscreen_data['']
    for ID, item in greenscreen_data.items():
        item.save(greenscreen_file_path)
    return greenscreen_data


def print_statistics(greenscreen_data):

    # compute basic statistics
    benchmark_counts = [item.data['benchmark'] for
                        item in greenscreen_data.values()]
    print('Provisional Benchmarks:')
    print('Provisional Benchmark 1: %d' %
          benchmark_counts.count('Benchmark 1'))
    print('Provisional Benchmark 2: %d' %
          benchmark_counts.count('Benchmark 2'))
    print('Provisional Benchmark 3: %d' %
          benchmark_counts.count('Benchmark 3'))
    print('Provisional Benchmark 4: %d' %
          benchmark_counts.count('Benchmark 4'))
    print('Provisional Benchmark U: %d' %
          benchmark_counts.count('Benchmark U'))

    print('List Translation Results:')

    invalid_cas_numbers = 0
    counts_available = []
    for item in greenscreen_data.values():
        hazard_counts = \
            len([hazard for hazard in item.data['hazards'].values() if
                 hazard['hazard_rating']])
        counts_available.append(hazard_counts)
        # if hazard_counts == 0:
        #     print('No hazards found in: ', item.data['cas_number'])
        if not item.data['cas_number_is_valid']:
            invalid_cas_numbers += 1
            print('Invalid CAS Number found:', item.data['cas_number'])

    print('Max number hazards available:', max(counts_available))
    print('Minimum number hazards available:', min(counts_available))
    print('Average number of hazards available:',
          sum(counts_available) / len(counts_available))
    print('Invalid CAS Numbers found:', invalid_cas_numbers)


if __name__ == "__main__":
    t = time.time()
    greenscreen_file_path = 'data/greenscreen_data'
    ghs_japan_file_path = 'data/ghs_json_data'
    prop65_file_path = 'data/prop65_data'
    greenscreen_data = {}

    greenscreen_data = bulk_ghs_japan_import(
        ghs_japan_file_path,
        greenscreen_file_path,
        greenscreen_data=greenscreen_data)
    print_statistics(greenscreen_data)
    print('Time elapsed: %d seconds' % (time.time() - t))

    greenscreen_data = bulk_prop65_import(
        prop65_file_path,
        greenscreen_file_path,
        greenscreen_data=greenscreen_data)
    print_statistics(greenscreen_data)
    print('Time elapsed: %d seconds' % (time.time() - t))
