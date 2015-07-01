#!/usr/bin/env python3

import time
import string

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

XML functionality requires the lxml module, available for download at
http://lxml.de

The lxml XML toolkit is a Pythonic binding for the C libraries
libxml2 and libxslt. It is unique in that it combines the speed
and XML feature completeness of these libraries with the simplicity
of a native Python API, mostly compatible but superior to the
well-known ElementTree API.

Note that the lxml toolkit is included as part of the enthought python
distribution. For other python distributions, the toolkit may need to be
installed. libxml2 and libxsl2 C libraries may also need to be
installed or updated. Refer to http://lxml.de for
more information.

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


class GHSJapan(object):
    '''
    description
    '''
    def __init__(self, sheet):
        '''
        Class constructor
        '''

        ghs_physical_hazards = (['explosives',
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
                                 'corrosive_to_metals'])

        ghs_health_hazards = (['acute_toxicity_oral',
                               'acute_toxicity_dermal',
                               'acute_toxicity_inhalation_gas',
                               'acute_toxicity_inhalation_vapor',
                               'acute_toxicity_inhalation_dust',
                               'skin_corrosion_irritation',
                               'serious_eye_damage_irritation',
                               'respiratory_skin_sensitizer',
                               'germ_cell_mutagenicity',
                               'carcinogenicity',
                               'toxic_to_reproduction',
                               'systemic_toxicity_single_exposure',
                               'systemic_toxicity_repeat_exposure',
                               'aspiration_hazard'])

        ghs_environmental_hazards = (['acute_aquatic_toxicity',
                                      'chronic_aquatic_toxicity'])

        absolute_pos_fields = {'cas_no': [3, 'C'],
                               'descriptive_name': [4, 'C'],
                               'date_classified': [3, 'H'],
                               'ID': [3, 'C']}

        calculated_fields = {'date_imported': time.ctime(),
                             'country': 'Japan'}

        hzd_sub_traits = ([['hazard_name', 'C'],
                           ['hazard_id', 'B'],
                           ['classification', 'D'],
                           ['hazard_statement', 'G'],
                           ['rationale', 'H'],
                           ['signal_word', 'F'],
                           ['symbol', 'E']])

        row_ind = [[range(8, 24)], [range(27, 42)], [range(45, 47)]]


        for key, row in zip([ghs_physical_hazards, ghs_health_hazards,
                             ghs_environmental_hazards], row_ind):
            print(key, row_ind)


        self.cas_number = \
            sheet.cell_value(
                absolute_pos_fields[0][1] - 1,
                self.excel_col_to_num(absolute_pos_fields[0][2]))

        self.data = {}
        self.data["hazards"] = {}

        for key, row, column in self.absolute_pos_fields:
            self.data[key] = \
                sheet.cell_value(row - 1,
                                 self.excel_col_to_num(column))

        for key, value in calculated_fields:
            self.data[key] = value

        for i in range(len(hzd_traits)):
            for j in range(len(hzd_traits[i][0])):
                row = hzd_traits[i][1][j] - 1
                hazard_subtraits = {}
                for sub in hzd_sub_traits:
                    col = excel_col_to_num(sub[1])
                    val = sheet.cell_value(row, col)
                    if type(val) is str:
                        # remove extraneous japanese characters from text
                        val = val.replace(u'\xf6', u'')
                        val = val.replace(u'\xba', u'')

                    hazard_subtraits[sub[0]] = [val]

                    if sub[0] == "hazard_name":
                        current_cas['hazards'][
                            hzd_traits[i][0][j]][
                            sub[0]].append(hzd_traits[i][0][j])
                    else:
                        current_cas['hazards'][hzd_traits[i][0][
                            j]][sub[0]].append(val)

        for element in absolute_pos_fields:
            if element[0] == 'cas_no':
                cas_no = sheet.cell_value(element[1] - 1,
                                          excel_col_to_num(
                                          element[2]))

            data[element[0]] = [sheet.cell_value(element[1] - 1,
                                excel_col_to_num(element[2]))]

        for element in calculated_fields:
            data[element[0]] = [element[1]]

        for i in range(len(hzd_traits)):
            for j in range(len(hzd_traits[i][0])):
                row = hzd_traits[i][1][j] - 1
                hazard_subtraits = {}
                for sub in hzd_sub_traits:
                    col = excel_col_to_num(sub[1])
                    val = sheet.cell_value(row, col)
                    if type(val) is str:
                        val = val.replace(u'\xf6', u'')
                        val = val.replace(u'\xba', u'')

                    hazard_subtraits[sub[0]] = [val]
                    if sub[0] == "hazard_name":
                        hazard_subtraits[sub[0]] = [hzd_traits[
                                                    i][0][j]]
                    else:
                        hazard_subtraits[sub[0]] = [val]

                hazard_traits[hzd_traits[i][0][j]] = \
                    hazard_subtraits


        # This print statement demonstrates how data can be accessed
        # after converting to JSON
        # print(json.dumps(total_data['6-85-2']['hazards']['explosives'],
        # indent=2))

    def excel_col_to_num(self, c):
        '''utility to convert excel row/column indices to Python row/column
        indices'''
        sum_ = 0
        for l in c:
            if l not in string.ascii_letters:
                return False
            sum_ *= 26
            sum_ += ord(l.upper()) - 64
        return sum_ - 1

if __name__ == "__main__":
