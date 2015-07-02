#!/usr/bin/env python3

import sys
import os.path
import xlrd
import string
import time
import getpass
import json
import re
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
            self.data = {}
            self.cas_number = None
            self.data['cas_number'] = None
            self.data['cas_number_is_valid'] = None
            self.data['warning'] = []
            self.data['descriptive_name'] = []
            for key in ['AA', 'AT', 'C', 'CA', 'D', 'F', 'IrE',
                        'M', 'N_r', 'N_s', 'R', 'Rx', 'ST_r', 'ST_s',
                        'SnR', 'SnS', 'E', 'P', 'B']:
                self.data[key] = {
                    'date_imported': [],
                    'imported_by': [],
                    'date_classified': [],
                    'source': [],
                    'list_type': [],
                    'list_rating': [],
                    'hazard_rating': [],
                    'overall_hazard_rating': 0}

    def import_ghs_japan_data(self, ghs_japan_data):
        '''
        This function imports/translates data from GHSJapanData object into a
        GreenScreenData object.
        '''

        self.ghs_japan_criteria = {}
        self.ghs_japan_criteria['1'] = {}
        self.ghs_japan_criteria['1']['Category 1A'] = 4
        self.ghs_japan_criteria['1']['Category 1B'] = 4
        self.ghs_japan_criteria['1']['Category 2'] = 3
        self.ghs_japan_criteria['1']['Not classified'] = 2

        self.ghs_japan_criteria['2'] = {}
        self.ghs_japan_criteria['2']['Category 1'] = 5
        self.ghs_japan_criteria['2']['Category 2'] = 5
        self.ghs_japan_criteria['2']['Category 3'] = 4
        self.ghs_japan_criteria['2']['Category 4'] = 3
        self.ghs_japan_criteria['2']['Category 5'] = 2
        self.ghs_japan_criteria['2']['Not classified'] = 2

        self.ghs_japan_criteria['3'] = {}
        self.ghs_japan_criteria['3']['Category 1'] = 5
        self.ghs_japan_criteria['3']['Category 2'] = 4
        self.ghs_japan_criteria['3']['Category 3'] = 3
        self.ghs_japan_criteria['3']['Not classified'] = 2

        self.ghs_japan_criteria['4'] = {}
        self.ghs_japan_criteria['4']['Category 1'] = 4
        self.ghs_japan_criteria['4']['Category 2'] = 3
        self.ghs_japan_criteria['4']['Not classified'] = 2

        self.ghs_japan_criteria['5'] = {}
        self.ghs_japan_criteria['5']['Category 1A'] = 4
        self.ghs_japan_criteria['5']['Category 1B'] = 3
        self.ghs_japan_criteria['5']['Not classified'] = 2
        self.ghs_japan_criteria['5']['Category1'] = 4

        self.ghs_japan_criteria['6'] = {}
        self.ghs_japan_criteria['6']['Category 1'] = 5
        self.ghs_japan_criteria['6']['Category 2A'] = 4
        self.ghs_japan_criteria['6']['Category 2B'] = 3
        self.ghs_japan_criteria['6']['Not classified'] = 2

        self.ghs_japan_criteria['7'] = {}
        self.ghs_japan_criteria['7']['Category 4'] = 3

        self.ghs_japan_criteria['8'] = {}
        self.ghs_japan_criteria['8']['Not classified'] = 2

        self.ghs_japan_criteria['9'] = {}
        self.ghs_japan_criteria['9']['Category 1'] = 3
        self.ghs_japan_criteria['9']['Not classified'] = 2

        self.ghs_japan_criteria['10'] = {}
        self.ghs_japan_criteria['10']['Category 1'] = 5
        self.ghs_japan_criteria['10']['Category 2'] = 4
        self.ghs_japan_criteria['10']['Category 3'] = 3
        self.ghs_japan_criteria['10']['Category 4'] = 3
        self.ghs_japan_criteria['10']['Not classified'] = 2

        self.ghs_japan_criteria['11'] = {}
        self.ghs_japan_criteria['11']['Category 1'] = 4
        self.ghs_japan_criteria['11']['Not classified'] = 2

        self.ghs_japan_criteria['12'] = {}
        self.ghs_japan_criteria['12']['Category 1'] = 4
        self.ghs_japan_criteria['12']['Category 2'] = 3
        self.ghs_japan_criteria['12']['Category A'] = 3
        self.ghs_japan_criteria['12']['Category B'] = 2
        self.ghs_japan_criteria['12']['Not classified'] = 2

        self.ghs_japan_criteria['13'] = {}
        self.ghs_japan_criteria['13']['Category 1'] = 4
        self.ghs_japan_criteria['13']['Category 2'] = 3
        self.ghs_japan_criteria['13']['Category 3'] = 2
        self.ghs_japan_criteria['13']['Not classified'] = 2

        # GHS Japan has some entries with empty CAS numbers, ignore these
        if ghs_japan_data.cas_number is "":
            print("Empty CAS number with ID: %s", ghs_japan_data.data['ID'])

        # validate cas number
        validated = all([self.validate_cas(cas)
                         for cas in ghs_japan_data.cas_number])
        if validated:
            self.data['cas_number_is_valid'] = True
        else:
            self.data['warning'].append(
                'Entry contains an invalid CAS number.')
            self.data['cas_number_is_valid'] = False

        self.data['cas_number'] = ghs_japan_data['cas_number']
        self.data['descriptive_name'].append(
            ghs_japan_data['descriptive_name'])
        if not self.data['ID']:
            self.data['ID'] = ghs_japan_data['ID']

        # for hazard in ghs_japan_data['hazards']:
        #     # Acute aquatic toxicity
        #     if hazard == "acute_aquatic_toxicity":
        #         cas_data['AA'] = \
        #             self.translate_ghs_japan(
        #                 ghs_japan_data, 'AA', CAS,
        #                 hazard, 'Ecotoxicity', 3)
        #
        #         # Final hazard rating created here, if there is a
        #         # previous GS JSON then we'll need to append instead
        #         # for now, we will declare hazard rating
        #         cas_data['AA']['hazard_rating'] = []
        #
        #         for x in \
        #                 range(0,
        #                       len(cas_data['AA']['hazard_rating_temp'])):
        #             try:
        #                 rating = int(cas_data['AA']['hazard_rating_temp'][x])
        #             except ValueError:
        #                 rating = int(cas_data['AA']['hazard_rating_temp'][x][2])
        #             cas_data['AA']['hazard_rating'].append(rating)
        #
        #         del cas_data['AA']['hazard_rating_temp']
        #         cas_data['AA']['overall_hazard_rating'] = \
        #             max(cas_data['AA']['hazard_rating'])
        #
        #     ## Acute Mammalian Toxicity
        #     elif hazard == "acute_toxicity_oral":
        #         cas_data['AT'] = \
        #             jsonify_hazard(json_data, cas_data, 'AT', CAS,
        #                            hazard, 'Group II and II* Human',
        #                            criteria_2)
        #
        #     elif hazard == "acute_toxicity_dermal":
        #         cas_data['AT'] = \
        #             jsonify_hazard(json_data, cas_data, 'AT', CAS,
        #                            hazard, 'Group II and II* Human',
        #                            criteria_2)
        #
        #     elif hazard == "acute_toxicity_inhalation_gas":
        #         cas_data['AT'] = \
        #             jsonify_hazard(json_data, cas_data, 'AT', CAS,
        #                            hazard, 'Group II and II* Human',
        #                            criteria_2)
        #
        #     elif hazard == "acute_toxicity_inhalation_vapor":
        #         cas_data['AT'] = \
        #             jsonify_hazard(json_data, cas_data, 'AT', CAS,
        #                            hazard, 'Group II and II* Human',
        #                            criteria_2)
        #
        #     elif hazard == "acute_toxicity_inhalation_dust":
        #         cas_data['AT'] = \
        #             jsonify_hazard(json_data, cas_data, 'AT', CAS,
        #                            hazard, 'Group II and II* Human',
        #                            criteria_2)
        #
        #     ## Carcinogenicity
        #     elif hazard == "carcinogenicity":
        #         cas_data['C'] = \
        #             jsonify_hazard(json_data, cas_data, 'C', CAS,
        #                            hazard, 'Group I', criteria_1)
        #
        #         cas_data['C']['hazard_rating'] = []
        #
        #         for x in \
        #                 range(0,
        #                       len(cas_data['C']['hazard_rating_temp'])):
        #             try:
        #                 rating = int(cas_data['C']['hazard_rating_temp'][x])
        #             except ValueError:
        #                 rating = int(cas_data['C']['hazard_rating_temp'][x][2])
        #
        #             cas_data['C']['hazard_rating'].append(rating)
        #         del cas_data['C']['hazard_rating_temp']
        #         cas_data['C']['overall_hazard_rating'] = \
        #             max(cas_data['C']['hazard_rating'])
        #
        #     ## Chronic Aquatic Toxicity
        #     elif hazard == "chronic_aquatic_toxicity":
        #         cas_data['CA'] = \
        #             jsonify_hazard(json_data, cas_data, 'CA', CAS,
        #                            hazard, 'Ecotoxicity', criteria_7)
        #
        #         cas_data['CA']['hazard_rating'] = []
        #
        #         for x in range(0, len(cas_data['CA']['hazard_rating_temp'])):
        #             try:
        #                 rating = int(cas_data['CA']['hazard_rating_temp'][x])
        #             except ValueError:
        #                 rating = int(cas_data['CA']['hazard_rating_temp'][x][2])
        #
        #             cas_data['CA']['hazard_rating'].append(rating)
        #
        #         del cas_data['CA']['hazard_rating_temp']
        #         cas_data['CA']['overall_hazard_rating'] = \
        #             max(cas_data['CA']['hazard_rating'])
        #
        #     ## Developmental or Reproductive
        #     elif hazard == "toxic_to_reproduction":
        #         cas_data['D'] = \
        #             jsonify_hazard(json_data, cas_data, 'D', CAS,
        #                            hazard, 'Group I', criteria_1)
        #
        #         cas_data['D']['hazard_rating'] = []
        #
        #         for x in range(0, len(cas_data['D']['hazard_rating_temp'])):
        #             try:
        #                 rating = int(cas_data['D']['hazard_rating_temp'][x])
        #             except ValueError:
        #                 rating = int(cas_data['D']['hazard_rating_temp'][x][2])
        #
        #             cas_data['D']['hazard_rating'].append(rating)
        #
        #         del cas_data['D']['hazard_rating_temp']
        #         cas_data['D']['overall_hazard_rating'] = \
        #             max(cas_data['D']['hazard_rating'])
        #
        #         cas_data['R'] = \
        #             jsonify_hazard(json_data, cas_data, 'R', CAS,
        #                            hazard, 'Group I', 1)
        #
        #         cas_data['R']['hazard_rating'] = []
        #
        #         for x in range(0, len(cas_data['R']['hazard_rating_temp'])):
        #             try:
        #                 rating = int(cas_data['R']['hazard_rating_temp'][x])
        #             except ValueError:
        #                 rating = int(cas_data['R']['hazard_rating_temp'][x][2])
        #
        #             cas_data['R']['hazard_rating'].append(rating)
        #
        #         del cas_data['R']['hazard_rating_temp']
        #         cas_data['R']['overall_hazard_rating'] = \
        #             max(cas_data['R']['hazard_rating'])
        #
        #     ## Flammability
        #     elif hazard == "flammable_liquids":
        #         cas_data['F'] = \
        #             jsonify_hazard(json_data, cas_data, 'F', CAS,
        #                            hazard, 'flammability', criteria_10)
        #
        #     elif hazard == "flammable_gases":
        #         cas_data['F'] = \
        #             jsonify_hazard(json_data, cas_data, 'F', CAS,
        #                            hazard, 'flammability', criteria_12)
        #
        #     elif hazard == "flammable_solids":
        #         cas_data['F'] = \
        #             jsonify_hazard(json_data, cas_data, 'F', CAS,
        #                            hazard, 'flammability', criteria_4)
        #
        #     elif hazard == "flammable_aerosols":
        #         cas_data['F'] = \
        #             jsonify_hazard(json_data, cas_data, 'F', CAS,
        #                            hazard, 'flammability', criteria_13)
        #
        #     elif hazard == "pyrophoric_liquids":
        #         cas_data['F'] = \
        #             jsonify_hazard(json_data, cas_data, 'F', CAS,
        #                            hazard, 'flammability', criteria_11)
        #
        #     elif hazard == "pyrophoric_solids":
        #         cas_data['F'] = \
        #             jsonify_hazard(json_data, cas_data, 'F', CAS,
        #                            hazard, 'flammability', criteria_11)
        #
        #     ## Eye Irritation
        #     elif hazard == "serious_eye_damage_irritation":
        #
        #         cas_data['IrE'] = \
        #             jsonify_hazard(json_data, cas_data, 'IrE', CAS,
        #                            hazard, 'Group II & II*', criteria_6)
        #
        #         cas_data['IrE']['hazard_rating'] = []
        #
        #         for x in \
        #             range(0,
        #                   len(cas_data['IrE']['hazard_rating_temp'])):
        #             try:
        #                 rating = int(cas_data['IrE']['hazard_rating_temp'][x])
        #             except ValueError:
        #                 rating = int(cas_data['IrE']['hazard_rating_temp'][x][2])
        #
        #             cas_data['IrE']['hazard_rating'].append(rating)
        #
        #         del cas_data['IrE']['hazard_rating_temp']
        #         cas_data['IrE']['overall_hazard_rating'] = \
        #             max(cas_data['IrE']['hazard_rating'])
        #
        #     ## Skin Irritation
        #     elif hazard == "skin_corrosion_irritation":
        #         cas_data['IrS'] = \
        #             jsonify_hazard(json_data, cas_data, 'IrS', CAS,
        #                            hazard, 'Group II & II*', criteria_3)
        #
        #         cas_data['IrS']['hazard_rating'] = []
        #
        #         for x in \
        #             range(0,
        #                   len(cas_data['IrS']['hazard_rating_temp'])):
        #             try:
        #                 rating = int(cas_data['IrS']['hazard_rating_temp'][x])
        #             except ValueError:
        #                 rating = int(cas_data['IrS']['hazard_rating_temp'][x][2])
        #
        #             cas_data['IrS']['hazard_rating'].append(rating)
        #
        #         del cas_data['IrS']['hazard_rating_temp']
        #         cas_data['IrS']['overall_hazard_rating'] = \
        #             max(cas_data['IrS']['hazard_rating'])
        #
        #     ## Mutagenicity/Genotoxicity
        #     elif hazard == "germ_cell_mutagenicity":
        #         cas_data['M'] = \
        #             jsonify_hazard(json_data, cas_data, 'M', CAS,
        #                            hazard, 'Group I', criteria_1)
        #
        #         cas_data['M']['hazard_rating'] = []
        #
        #         for x in \
        #             range(0,
        #                   len(cas_data['M']['hazard_rating_temp'])):
        #             try:
        #                 rating = int(cas_data['M']['hazard_rating_temp'][x])
        #             except ValueError:
        #                 rating = int(cas_data['M']['hazard_rating_temp'][x][2])
        #
        #             cas_data['M']['hazard_rating'].append(rating)
        #
        #         del cas_data['M']['hazard_rating_temp']
        #         cas_data['M']['overall_hazard_rating'] = \
        #             max(cas_data['M']['hazard_rating'])
        #
        #     ## Neurotoxicity and Systemic Toxicity are in one entry in
        #     #  the Japan database, separated by keywords.
        #
        #     ## Single Exposure
        #     elif hazard == "systemic_toxicity_single_exposure":
        #         cas_data['N_s'] = \
        #             jsonify_hazard(json_data, cas_data, 'N_s', CAS,
        #                            hazard, 'Group II & II*', criteria_3)
        #
        #         cas_data['N_s']['hazard_rating'] = []
        #
        #         for x in \
        #             range(0,
        #                   len(cas_data['N_s']['hazard_rating_temp'])):
        #             try:
        #                 rating = int(cas_data['N_s']['hazard_rating_temp'][x])
        #             except ValueError:
        #                 rating = int(cas_data['N_s']['hazard_rating_temp'][x][2])
        #
        #             cas_data['N_s']['hazard_rating'].append(rating)
        #
        #         del cas_data['N_s']['hazard_rating_temp']
        #         cas_data['N_s']['overall_hazard_rating'] = \
        #             max(cas_data['N_s']['hazard_rating'])
        #
        #         cas_data['ST_s'] = \
        #             jsonify_hazard(json_data, cas_data, 'ST_s', CAS,
        #                            hazard, 'Group II & II*', criteria_3)
        #
        #         cas_data['ST_s']['hazard_rating'] = []
        #
        #         for x in range(0, len(cas_data['ST_s']['hazard_rating_temp'])):
        #             try:
        #                 rating = int(cas_data['ST_s']['hazard_rating_temp'][x])
        #             except ValueError:
        #                 rating = int(cas_data['ST_s']['hazard_rating_temp'][x][2])
        #
        #             cas_data['ST_s']['hazard_rating'].append(rating)
        #
        #         del cas_data['ST_s']['hazard_rating_temp']
        #         cas_data['ST_s']['overall_hazard_rating'] = \
        #             max(cas_data['ST_s']['hazard_rating'])
        #
        #     ## Repeat Exposure
        #     elif hazard == "systemic_toxicity_repeat_exposure":
        #         cas_data['N_r'] = \
        #             jsonify_hazard(json_data, cas_data, 'N_r', CAS,
        #                            hazard, 'Group II & II*', criteria_4)
        #
        #         cas_data['N_r']['hazard_rating'] = []
        #
        #         for x in range(0, len(cas_data['N_r']['hazard_rating_temp'])):
        #             try:
        #                 rating = int(cas_data['N_r']['hazard_rating_temp'][x])
        #             except ValueError:
        #                 rating = int(cas_data['N_r']['hazard_rating_temp'][x][2])
        #
        #             cas_data['N_r']['hazard_rating'].append(rating)
        #
        #         del cas_data['N_r']['hazard_rating_temp']
        #         cas_data['N_r']['overall_hazard_rating'] = \
        #             max(cas_data['N_r']['hazard_rating'])
        #
        #         cas_data['ST_r'] = \
        #             jsonify_hazard(json_data, cas_data, 'ST_r', CAS,
        #                            hazard, 'Group II & II*', criteria_4)
        #
        #         cas_data['ST_r']['hazard_rating'] = []
        #
        #         for x in range(0, len(cas_data['ST_r']['hazard_rating_temp'])):
        #             try:
        #                 rating = int(cas_data['ST_r']['hazard_rating_temp'][x])
        #             except ValueError:
        #                 rating = int(cas_data['ST_r']['hazard_rating_temp'][x][2])
        #
        #             cas_data['ST_r']['hazard_rating'].append(rating)
        #
        #         del cas_data['ST_r']['hazard_rating_temp']
        #         cas_data['ST_r']['overall_hazard_rating'] = \
        #             max(cas_data['ST_r']['hazard_rating'])
        #
        #     ## Reactivity
        #     elif hazard == "explosives":
        #         cas_data['Rx'] = \
        #             jsonify_hazard(json_data, cas_data, 'Rx', CAS,
        #                            hazard, 'Physical', criteria_8)
        #
        #     elif hazard == "self_reactive_substances":
        #         cas_data['Rx'] = \
        #             jsonify_hazard(json_data, cas_data, 'Rx', CAS,
        #                            hazard, 'Physical', criteria_8)
        #
        #     elif hazard == \
        #             "substances_mixtures_emit_flammable_gas_in_contact_with_water":
        #         cas_data['Rx'] = \
        #             jsonify_hazard(json_data, cas_data, 'Rx', CAS,
        #                            hazard, 'Physical', criteria_3)
        #
        #     elif hazard == "oxidizing_gases":
        #         cas_data['Rx'] = \
        #             jsonify_hazard(json_data, cas_data, 'Rx', CAS,
        #                            hazard, 'Physical', criteria_11)
        #
        #     elif hazard == "oxidizing_liquids":
        #         cas_data['Rx'] = \
        #             jsonify_hazard(json_data, cas_data, 'Rx', CAS,
        #                            hazard, 'Physical', criteria_3)
        #
        #     elif hazard == "oxidizing_solids":
        #         cas_data['Rx'] = \
        #             jsonify_hazard(json_data, cas_data, 'Rx', CAS,
        #                            hazard, 'Physical', criteria_3)
        #
        #     elif hazard == "organic_peroxides":
        #         cas_data['Rx'] = \
        #             jsonify_hazard(json_data, cas_data, 'Rx', CAS,
        #                            hazard, 'Physical', criteria_8)
        #
        #     elif hazard == "self_heating_substances":
        #         cas_data['Rx'] = \
        #             jsonify_hazard(json_data, cas_data, 'Rx', CAS,
        #                            hazard, 'Physical', criteria_4)
        #
        #     elif hazard == "corrosive_to_metals":
        #         cas_data['Rx'] = \
        #             jsonify_hazard(json_data, cas_data, 'Rx', CAS,
        #                            hazard, 'Physical', criteria_9)
        #
        #     ## Respiratory Sensitization/Skin Sensitization
        #     #  These hazards are together in one cell in the GHS Japan
        #     #  excel sheet
        #     elif hazard == "respiratory_skin_sensitizer":
        #         cas_data['SnR'] = \
        #             jsonify_hazard(json_data, cas_data, 'SnR', CAS,
        #                            hazard, 'Group II & II*', criteria_5)
        #
        #         cas_data['SnR']['hazard_rating'] = []
        #
        #         for x in \
        #             range(0,
        #                   len(cas_data['SnR']['hazard_rating_temp'])):
        #             try:
        #                 rating = int(cas_data['SnR']['hazard_rating_temp'][x])
        #             except ValueError:
        #                 rating = int(cas_data['SnR']['hazard_rating_temp'][x][2])
        #
        #             cas_data['SnR']['hazard_rating'].append(rating)
        #
        #         del cas_data['SnR']['hazard_rating_temp']
        #         cas_data['SnR']['overall_hazard_rating'] = \
        #             max(cas_data['SnR']['hazard_rating'])
        #
        #         cas_data['SnS'] = \
        #             jsonify_hazard(json_data, cas_data, 'SnS', CAS,
        #                            hazard, 'Group II & II*', criteria_5)
        #
        #         cas_data['SnS']['hazard_rating'] = []
        #
        #         for x in \
        #             range(0,
        #                   len(cas_data['SnS']['hazard_rating_temp'])):
        #             try:
        #                 rating = int(cas_data['SnS']['hazard_rating_temp'][x])
        #             except ValueError:
        #                 rating = int(cas_data['SnS']['hazard_rating_temp'][x][2])
        #
        #             cas_data['SnS']['hazard_rating'].append(rating)
        #
        #         del cas_data['SnS']['hazard_rating_temp']
        #         cas_data['SnS']['overall_hazard_rating'] = \
        #             max(cas_data['SnS']['hazard_rating'])
        #
        # ## This section is needed for the CAS hazards with multiple
        # # sources from Japan. For example, Japan has 5 categories
        # # that correspond to Acute Mammalian Toxicity
        #
        # cas_data['AT']['hazard_rating'] = []
        # cas_data['AT']['hazard_rating_1'] = []
        # cas_data['AT']['hazard_rating_2'] = []
        #
        # for x in range(0, len(cas_data['AT']['hazard_rating_temp'])):
        #     try:
        #         rating_1 = int(cas_data['AT']['hazard_rating_temp'][x])
        #         cas_data['AT']['hazard_rating_1'].append(rating_1)
        #     except ValueError:
        #         rating_2 = int(cas_data['AT']['hazard_rating_temp'][x][2])
        #         cas_data['AT']['hazard_rating_2'].append(rating_2)
        #
        # rating_3 = max(cas_data['AT']['hazard_rating_1'])
        # cas_data['AT']['hazard_rating'].append(rating_3)
        #
        # rating_4 = cas_data['AT']['hazard_rating_2']
        # if rating_4:
        #     cas_data['AT']['hazard_rating'].append(max(rating_4))
        #
        # cas_data['AT']['overall_hazard_rating'] = \
        #     max(cas_data['AT']['hazard_rating'])
        #
        # del cas_data['AT']['hazard_rating_temp']
        # del cas_data['AT']['hazard_rating_1']
        # del cas_data['AT']['hazard_rating_2']
        #
        # cas_data['F']['hazard_rating'] = []
        # cas_data['F']['hazard_rating_1'] = []
        # cas_data['F']['hazard_rating_2'] = []
        #
        # for x in range(0, len(cas_data['F']['hazard_rating_temp'])):
        #     try:
        #         rating_1 = int(cas_data['F']['hazard_rating_temp'][x])
        #         cas_data['F']['hazard_rating_1'].append(rating_1)
        #     except ValueError:
        #         rating_2 = int(cas_data['F'][
        #             'hazard_rating_temp'][x][2])
        #         cas_data['F']['hazard_rating_2'].append(rating_2)
        #
        # rating_3 = max(cas_data['F']['hazard_rating_1'])
        # cas_data['F']['hazard_rating'].append(rating_3)
        #
        # rating_4 = cas_data['F']['hazard_rating_2']
        # if rating_4:
        #     cas_data['F']['hazard_rating'].append(max(rating_4))
        #
        # cas_data['F']['overall_hazard_rating'] = \
        #     max(cas_data['F']['hazard_rating'])
        #
        # del cas_data['F']['hazard_rating_temp']
        # del cas_data['F']['hazard_rating_1']
        # del cas_data['F']['hazard_rating_2']
        #
        # cas_data['Rx']['hazard_rating'] = []
        # cas_data['Rx']['hazard_rating_1'] = []
        # cas_data['Rx']['hazard_rating_2'] = []
        #
        # for x in range(0, len(cas_data['Rx']['hazard_rating_temp'])):
        #     try:
        #         rating_1 = int(cas_data['Rx']['hazard_rating_temp'][x])
        #         cas_data['Rx']['hazard_rating_1'].append(rating_1)
        #     except ValueError:
        #         rating_2 = int(cas_data['Rx'][
        #             'hazard_rating_temp'][x][2])
        #         cas_data['Rx']['hazard_rating_2'].append(rating_2)
        #
        # rating_3 = max(cas_data['Rx']['hazard_rating_1'])
        # cas_data['Rx']['hazard_rating'].append(rating_3)
        #
        # rating_4 = cas_data['Rx']['hazard_rating_2']
        # if rating_4:
        #     cas_data['Rx']['hazard_rating'].append(max(rating_4))
        #
        # cas_data['Rx']['overall_hazard_rating'] = \
        #     max(cas_data['Rx']['hazard_rating'])
        #
        # del cas_data['Rx']['hazard_rating_temp']
        # del cas_data['Rx']['hazard_rating_1']
        # del cas_data['Rx']['hazard_rating_2']
        #
        # total_data[json_data[CAS]['cas_no'][0]] = cas_data

    def validate_cas(self, cas):
        '''
        CAS Validation has two steps:
        Step 1: Verify that the number is formatted correctly (2-7 digits)-
                (1-2 digits)-(1 check sum digit)
        Step 2: Verify that the check sum is the correct amount when compared to
                the remainder of the rest of the numbers combined and multiplied
                according to the CAS validation system
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
        if total_valid_value % (10) == int(check_CAS):
            pass
        else:
            print("Invalid CAS: " + CAS)
            return False
        return True

    def benchmark(self):
        '''
        Find the max hazard rating and update benchmark scores. This section
        includes GreenScreen trumping criteria.
        '''
        self.trumping()

        AA = self.data['AA']['overall_hazard_rating']
        AT = self.data['AT']['overall_hazard_rating']
        C = self.data['C']['overall_hazard_rating']
        CA = self.data['CA']['overall_hazard_rating']
        D = self.data['D']['overall_hazard_rating']
        R = self.data['R']['overall_hazard_rating']
        F = self.data['F']['overall_hazard_rating']
        IrE = self.data['IrE']['overall_hazard_rating']
        IrS = self.data['IrS']['overall_hazard_rating']
        M = self.data['M']['overall_hazard_rating']
        N_s = self.data['N_s']['overall_hazard_rating']
        N_r = self.data['N_r']['overall_hazard_rating']
        Rx = self.data['Rx']['overall_hazard_rating']
        ST_s = self.data['ST_s']['overall_hazard_rating']
        ST_r = self.data['ST_r']['overall_hazard_rating']
        SnR = self.data['SnR']['overall_hazard_rating']
        SnS = self.data['SnS']['overall_hazard_rating']
        E = self.data['E']['overall_hazard_rating']
        P = self.data['P']['overall_hazard_rating']
        B = self.data['B']['overall_hazard_rating']

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
            json_data[CAS]['gs_benchmark'] = 'Benchmark 1'
            bench_numbers['1'] += 1

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
            json_data[CAS]['gs_benchmark'] = 'Benchmark 2'
            bench_numbers['2'] += 1

        ## Benchmark 3
        elif ((P >= 3) or  # moderate P
              (B >= 3) or  # moderate B
              (eco_T >= 3) or  # moderate eco_T
              (max([Group_2, Group_2_star]) >= 3) or  # moderate T
              (F >= 3) or  # moderate F
                (Rx >= 3)):  # moderate Rx
            json_data[CAS]['gs_benchmark'] = 'Benchmark 3'
            bench_numbers['3'] += 1

        ## Benchmark 4
        elif ((P <= 2) and  # low P
              (B <= 2) and  # low B
              (all_four_groups <= 2) and  # low four_groups
              (F <= 2) and
              (Rx <= 2) and
              (B != 0) and
              (T != 0) and
                (eco_T != 0)):  # moderate T
            json_data[CAS]['gs_benchmark'] = 'Benchmark 4'
            bench_numbers['4'] += 1

        else:
            json_data[CAS]['gs_benchmark'] = 'Benchmark U'
            bench_numbers['U'] += 1

    def trumping(self):
        for key in ['AA', 'AT', 'C', 'CA', 'D', 'F', 'IrE',
                    'M', 'N_r', 'N_s', 'R', 'Rx', 'ST_r', 'ST_s',
                    'SnR', 'SnS', 'E', 'P', 'B']:
            for list_rating in range(4, 0, -1):
                rating = \
                    [i for i, j in zip(
                        self.data[key]['hazard_rating'],
                        self.data[key]['list_rating']) if j is list_rating]
                if rating:
                    rating = max(rating)
                    break
            if rating:
                self.data[key]['overall_hazard_rating'] = rating
            else:
                self.data[key]['overall_hazard_rating'] = 0

    def translate_ghs_japan(self, hazard, ghs_japan_data, category, criteria):
        systemic_words = (['respiratory', 'blood', 'kidney', 'liver',
                           'adrenal', 'gastro', 'systemic', 'eye', 'heart',
                           'bone', 'hematop', 'cardio', 'spleen', 'thyroid',
                           'lung', 'gingi', 'testes'])

        self.data[hazard]['date_imported'].append(
            ghs_japan_data['date_imported'])
        self.data[hazard]['imported_by'].append(getpass.getuser())
        self.data[hazard]['date_classified'].append(
            ghs_japan_data['date_classified'])
        self.data[hazard]['source'].append(ghs_japan_data['source'])
        self.data[hazard]['list_type'].append(ghs_japan_data['list_type'])
        self.data[hazard]['list_rating'].append(ghs_japan_data['list_rating'])


        try:
            rating = 0

            # ST_s or ST_r will set use_ST to 1 if it finds a rating, this is
            # a special case where normal rating method is not used, instead an
            # if statement with ST_s or ST_r will set the rating
            use_ST = 0

            try:
                # Location is the variable name for the portion of the GHS data
                # that has the classification for this hazard.
                #
                #  Systemic toxicity is formatted inconsistently in the GHS
                #  Japan data. Some system toxicity classifications have a
                #  different format without semi colons and must be treated as
                #  a special case. The program attempts to handle most common
                #  formatting inconsistencies in the excel files
                no_semi = False

                if json_data[CAS]['hazards'][hazard][
                        'classification'][0].find(';') < 0:
                    no_semi = True

                Sn_class = json_data[CAS]['hazards'][hazard][
                    'classification'][0].split(';')

                if len(Sn_class) < 2:
                    Sn_class = \
                        json_data[CAS]['hazards'][hazard][
                            'classification'][0].split('\n')

                    if len(Sn_class) < 2:
                        Sn_class = \
                            json_data[CAS]['hazards'][hazard][
                                'classification'][0]
                        mid = Sn_class.find('Skin sensitizer')
                        part1 = Sn_class[0:mid]
                        part2 = Sn_class[mid:len(Sn_class)]
                        Sn_class = [part1, part2]
                        no_semi = False

                    else:
                        no_semi = False

                # Sometimes hazard classifications are split by a comma
                if json_data[CAS]['hazards'][hazard][
                        'classification'][0].find('),') >= 0:
                    no_semi = True

                # Sn_class_unsplit = \
                # json_data[CAS]['hazards'][hazard]['classification'][0]

                ## Special cases just for SnR, SnS, N_s, N_r, ST_s, ST_r
                if name == 'SnR':
                    location = Sn_class[0]

                elif name == 'SnS':

                    if Sn_class[0] == 'Classification not possible':
                        location = 'Classification not possible'
                    else:
                        try:
                            location = Sn_class[1]
                        except IndexError:
                            location = "Nothing here"
                            print("IndexError, Sn_class is ")
                            print(Sn_class)
                            print("CAS: " + CAS)
                            print("Name: " + name)

                elif name == 'N_s':

                    if len(Sn_class) < 2 or no_semi == 1:
                        Sn_class = \
                            json_data[CAS]['hazards'][hazard][
                                'classification'][0].split('),')

                    for part in Sn_class:
                        found = part.find('nervous')
                        if found >= 0:
                            location = part
                            break

                        else:
                            location = 'No data available'

                elif name == 'N_r':
                    if len(Sn_class) < 2 or no_semi == 1:
                        Sn_class = \
                            json_data[CAS]['hazards'][hazard][
                                'classification'][0].split('),')

                    for part in Sn_class:
                        found = part.find('nervous')
                        if found >= 0:
                            location = part
                            break

                        else:
                            location = 'No data available'

                elif name == 'ST_s':
                    max_rating = 0
                    if len(Sn_class) < 2 or no_semi == 1:
                        Sn_class = \
                            json_data[CAS]['hazards'][hazard][
                                'classification'][0].split('),')

                    for line in Sn_class:
                        for keyword in systemic_words:
                            if line.find(keyword) >= 0:
                                for crit in criteria:
                                    found = line.find(crit)
                                    if found >= 0:
                                        if criteria[crit] > max_rating:
                                            max_rating = criteria[crit]

                    rating = max_rating
                    use_ST = True

                elif name == 'ST_r':
                    max_rating = 0
                    if len(Sn_class) < 2 or no_semi == 1:
                        Sn_class = \
                            json_data[CAS]['hazards'][hazard][
                                'classification'][0].split('),')

                    for line in Sn_class:
                        for keyword in systemic_words:
                            if line.find(keyword) >= 0:
                                for crit in criteria:
                                    found = line.find(crit)
                                    if found >= 0:
                                        if criteria[crit] > max_rating:
                                            max_rating = criteria[crit]

                    rating = max_rating
                    use_ST = True

                # The normal case where the hazard is not one of the
                # six special cases
                else:
                    location = \
                        json_data[CAS]['hazards'][hazard]['classification'][0]

                if use_ST:
                    pass

                else:
                    for crit in criteria:
                        found = location.find(crit)
                        if found >= 0:
                            rating = criteria[crit]

            except KeyError:
                rating = '0'

            if hazard_dict['hazard_rating_temp']:
                hazard_dict['hazard_rating_temp'].append(rating)

        except KeyError:
            hazard_dict['hazard_rating_temp'] = [rating]

    hazard_dict['overall_hazard_rating'] = 0

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

        with open(os.path.join(data_dir, self.data['ID'] + 'json'), 'w') as f:
            json.dump(self.data, f, indent=4, sort_keys=True)

if __name__ == "__main__":
    # Time code execution
    t = time.time()

    # As of January 2015, the excel files are available at the GHS Japan
    # website at the following locations
    url = 'http://www.safe.nite.go.jp/english/ghs/files/'
    file_names = (['h25_mhlw_new_e.xls',
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
                   'h18_imcg_e.xls'])

    ## Specify where to save the data.
    #  If the directory does not exist, it will be created.
    #  You may also skip this step and download data manually.
    data_dir = 'data/'

    ##  Download the excel files from GHS Japan website.
    download_files(url, data_dir, file_names)

    ## Import GHS Japan Data: This step converts the excel files to an lxml
    #  data structure. First we need to specify which file in the list is the
    #  directory and which are the data files. This function was custom written
    #  around the format of the GHS_Japan Excel files. To import other
    #  databases it is necessary to develop additional import functions.
    ghs_japan_data_xml = \
        import_ghs_japan(file_names, data_dir, file_type='xml')
    ghs_japan_data_json = \
        import_ghs_japan(file_names, data_dir, file_type='json')

    ## Translate to Green Screen format.
    #  This function is also custom written for the ghs japan country list.
    #  Additional translation functions are necessary to translate from other
    #  libraries.
    gs_japan_data_json = translate_ghs_japan_json(ghs_japan_data_json)

    ## Run the GS Japan JSON data through the assessment function to create GS
    #  benchmarks
    gs_japan_data_json = gs_assessment_json(gs_japan_data_json)

    ## Export GHS JSON data
    data_dir = 'data/ghs_json_data/'
    save_json_individual(ghs_japan_data_json, data_dir)

    ## Export GS JSON data
    data_dir = 'data/gs_json_data/'
    save_json_individual_gs(gs_japan_data_json, data_dir)

    ## Export XML Data:
    data_dir = 'data/ghs_xml_data/'
    save_xml_individual(ghs_japan_data_xml, data_dir, 'ghs')
    save_xml_master(ghs_japan_data_xml, data_dir, 'ghs_master_list.xml')

    elapsed = time.time() - t
    print('Time elapsed: ', elapsed, ' seconds.')


if __name__ == "__main__":
    main()
