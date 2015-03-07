#!/usr/bin/env python

'''
greenscreen_tools.py

This program consists of a collection of tools for importing data from GreenScreen
databases, translating data to GreenScreen format and performing GreenScreen benchmark assessment. 
The present Python program can be executed directly, or any of the various modules can be used from 
within another Python program. Refer to the main() function at the end of the code for example usage.

Copyright 2013 Kristopher Wehage, Panan Chenhansa, Julie M. Schoenung
University of California-Davis

This code comes with no warantees or guarantee of fitness
for any purpose. 

XML functionality requires the lxml module, available for download at
http://lxml.de

The lxml XML toolkit is a Pythonic binding for the C libraries 
libxml2 and libxslt. It is unique in that it combines the speed 
and XML feature completeness of these libraries with the simplicity 
of a native Python API, mostly compatible but superior to the 
well-known ElementTree API. 

Note that the lxml toolkit is included as part of the enthought python
distribution. For other python distributions, the toolkit may need to be installed.
libxml2 and libxsl2 C libraries may also need to be
installed or updated. Refer to http://lxml.de for
more information.
'''

__author__ = '''Kristopher Wehage (ktwehage@ucdavis.edu)'''

from lxml import objectify
from lxml import etree
import sys
import urllib2
import os.path
import xlrd
import string
import time
import getpass
import json
import re


class InvalidCAS_Error( Exception ):
    pass


class MultipleSource_Error( Exception ):
    pass


#
# if files already exist in the 'data' folder, do nothing, if the files do not exist, 
# download them from specified URL.
#
def download_files(url, data_dir, file_names):
    def restart_line():
        sys.stdout.write('\r')
        sys.stdout.flush()
    data_dir_split = data_dir.split('/')
    cwd = os.getcwd()
    if data_dir_split[0] == '':
        os.chdir('/')
    for element in data_dir_split:
        if not element == '':
            if not os.path.exists(element):
                os.makedirs(element)
            os.chdir(element)
    for element in file_names:
        if not os.path.isfile(element):
            path_to_download = url + element
            u = urllib2.urlopen(path_to_download)
            f = open(element, 'wb')
            meta = u.info()
            filesize = int(meta.getheaders("Content-Length")[0])
            print("Downloading: %s Bytes: %s" % (element, filesize))
            filesize_dl = 0
            blocksize = 64*1024
            while True:
                buff = u.read(blocksize)
                if not buff:
                    break
                filesize_dl += len(buff)
                f.write(buff)
                status = r"%10d [%3.2f%%]" % (filesize_dl, filesize_dl * 100 / filesize)
                status = status + chr(8)*(len(status)+1)
                restart_line()
                sys.stdout.write(status)
            f.close()
    os.chdir(cwd)


#
# Convert Excel row/column to Python row/column indices                   
#
def excel_col_to_num(c):
    sum_ = 0
    for l in c:
        if not l in string.ascii_letters:
            return False
        sum_*=26
        sum_+=ord(l.upper())-64
    return sum_-1


#
# Use to import data from GHS_Japan data files to Python lxml format
#
def import_ghs_japan(ghs_data_files, data_dir, file_type):
    #
    # Note that indexing is assigned using Excel row/col convention for convenience, 
    # later this is converted to pythonic indexing for looking up within the excel file. 
    #

    ghs_physical_hazards = (['explosives','flammable_gases','flammable_aerosols',
                             'oxidizing_gases','gases_under_pressure','flammable_liquids',
                             'flammable_solids','self_reactive_substances','pyrophoric_liquids',
                             'pyrophoric_solids','self_heating_substances','substances_mixtures_emit_flammable_gas_in_contact_with_water',
                             'oxidizing_liquids','oxidizing_solids','organic_peroxides','corrosive_to_metals'])

    ghs_health_hazards = (['acute_toxicity_oral','acute_toxicity_dermal',
                           'acute_toxicity_inhalation_gas','acute_toxicity_inhalation_vapor',
                           'acute_toxicity_inhalation_dust','skin_corrosion_irritation',
                           'serious_eye_damage_irritation','respiratory_skin_sensitizer',
                           'germ_cell_mutagenicity','carcinogenicity','toxic_to_reproduction',
                           'systemic_toxicity_single_exposure','systemic_toxicity_repeat_exposure',
                           'aspiration_hazard'])

    ghs_environmental_hazards = (['acute_aquatic_toxicity','chronic_aquatic_toxicity'])


    absolute_pos_fields = ([['cas_no', 3, 'C'],
                            ['descriptive_name', 2, 'D'],
                            ['date_classified', 3, 'E'],
                            ['ID', 2, 'A']]
                            )

    calculated_fields = ([['date_imported', time.ctime()],
                          ['country', 'Japan']])

    hzd_sub_traits = ([['hazard_name', 'C'],
                       ['hazard_id', 'B'],
                       ['classification', 'D'], 
                       ['hazard_statement','G'],
                       ['rationale', 'H'],
                       ['signal_word','F'],
                       ['symbol','E']])

    hzd_temp_list = [[ghs_physical_hazards], [ghs_health_hazards], [ghs_environmental_hazards]]
    row_ind = [[range(6,22)], [range(25,39)], [range(42,44)]]
    hzd_type= ['physical', 'health', 'environmental']

    hzd_temp_list = [[ghs_physical_hazards], [ghs_health_hazards], [ghs_environmental_hazards]]
    row_ind = [[range(6,22)], [range(25,39)], [range(42,44)]]
    hzd_type= ['physical', 'health', 'environmental']
    hzd_traits = []

    ## Putting in hazard traits along with their locations on excel ex:explosives, chronic aquatic toxicity
    for i in range(len(hzd_temp_list)):
        for j in range(len(hzd_temp_list[i])):
            hzd_traits.append([hzd_temp_list[i][j], row_ind[i][j], hzd_type[i]])

    fields = []
    fields_temp = absolute_pos_fields + calculated_fields

    for element in fields_temp:
        fields.append(element[0])

    if file_type == 'xml':
        print('Importing GHS Japan in to XML format...')
        ghs_japan_data = objectify.Element('root', nsmap = {'ghs':'http://amrl.engr.ucdavis.edu/ghs_japan'})
        data = objectify.SubElement(ghs_japan_data,'ghs_data')

        for element in fields:
            objectify.SubElement(data,element) 

        for i in range(len(hzd_traits)):
            for j in range(len(hzd_traits[i][0])):
                str1 = str(hzd_traits[i][0][j])
                str2= str(hzd_traits[i][2])
                var = objectify.SubElement(data, str1, hazard_type=str2)
                for subelement in hzd_sub_traits:
                    str1=str(subelement[0])
                    objectify.SubElement(var, str1)
        
        ## ghs_data_files is the Excel sheet    
        for element in ghs_data_files:
            print('Loading data for ' + element + '.')
            book = xlrd.open_workbook(data_dir + '/' + element)
            for i in xrange(1,book.nsheets):
                sheet = book.sheet_by_index(i)
                cas_no_check = sheet.cell_value(absolute_pos_fields[0][1]-1,excel_col_to_num(absolute_pos_fields[0][2]))

                cas_no_ind = ghs_japan_data.xpath('/root/ghs_data/cas_no')

                ## This method appends new cas-no to the end of XML file. 
                ## Checking to see whether CAS_num is already in here
                if cas_no_check in cas_no_ind:
                    ind = cas_no_ind.index(cas_no_check)

                else:
                    data = objectify.SubElement(ghs_japan_data,'ghs_data')
                
                    for element in fields:
                        objectify.SubElement(data,element)  
                    for i in range(len(hzd_traits)):
                        for j in range(len(hzd_traits[i][0])):
                            str1 = str(hzd_traits[i][0][j])
                            str2= str(hzd_traits[i][2])
                            var = objectify.SubElement(data, str1, hazard_type=str2)
                            for subelement in hzd_sub_traits:
                                str1=str(subelement[0])
                                objectify.SubElement(var, str1)

                    ind = len(cas_no_ind)

                ghs_data_ind = 'ghs_data['+str(ind)+']'

                    ## the exec function below is a clumsy way to assign values to objectify object locations
                    ## programmatically, but necessary because objectify object values can only be
                    ## assigned if direct path is given.
                for element in absolute_pos_fields:
                    val = sheet.cell_value(element[1]-1,excel_col_to_num(element[2]))
                    exec('%s.%s.%s=%s' %('ghs_japan_data',ghs_data_ind,element[0],'val'))

                for element in calculated_fields:
                    ##  ghs_japan_data.index_number.calculated_main_fields = element's values
                    exec('%s.%s.%s="%s"' %('ghs_japan_data',ghs_data_ind,element[0],element[1]))

                ##  0->[0-15] 1->[0-14] 2->[0-1] 
                for i in range(len(hzd_traits)):
                    for j in range(len(hzd_traits[i][0])):
                        row = hzd_traits[i][1][j]-1 #convert to pythonic indexing here

                        for sub in hzd_sub_traits:
                            col = excel_col_to_num(sub[1])
                            val = sheet.cell_value(row,col)
                            if isinstance(val, unicode):
                                val = val.replace(u'\xf6', u'')
                                val = val.replace(u'\xba', u'')

                            ## ghs_japan_data.index_number.hazard_class.hazard_trait ex: chronic_aquatic_toxicity,hazard_name   
                            exec('%s.%s.%s.%s=%s' %('ghs_japan_data', ghs_data_ind, hzd_traits[i][0][j], sub[0], 'val'))

        print('Done.')
        return ghs_japan_data

    if file_type == 'json':
        print('Importing GHS Japan data to JSON...')

        # hzd_traits = []
        cas_no_ind = []
        total_data = {}

        # ## Putting in hazard traits along with their locations on excel (explosives, chronic aquatic toxicity, etc.)
        # for i in range(len(hzd_temp_list)):
        #     for j in range(len(hzd_temp_list[i])):
        #         hzd_traits.append([hzd_temp_list[i][j], row_ind[i][j], hzd_type[i]])

        # fields = []
        # fields_temp = absolute_pos_fields + calculated_fields
        # for element in fields_temp:
        #     fields.append(element[0])

        ## ghs_data_files is the Excel sheet    
        for element in ghs_data_files:
            print ('Loading data for ' + element + '.')
            book = xlrd.open_workbook(data_dir + '/' + element)
            for i in xrange(1,book.nsheets):
                sheet = book.sheet_by_index(i)
                cas_no_check = sheet.cell_value(absolute_pos_fields[0][1]-1,excel_col_to_num(absolute_pos_fields[0][2]))

                data = {}
                hazard_traits = {}

                #This method appends new cas-no to the end of JSON file. 
             
                # Checking to see whether CAS_num is already in here, normally this would be considered an error since
                # we have two conflicting sources of information, but we just import both for now. 
                if cas_no_check in cas_no_ind:
                    current_cas = total_data[cas_no_check]
             
                    for element in absolute_pos_fields:
                        data[element[0]] = sheet.cell_value(element[1]-1,excel_col_to_num(element[2]))
                        current_cas[element[0]].append(sheet.cell_value(element[1]-1,excel_col_to_num(element[2])))

                    for element in calculated_fields:
                        data[element[0]] = element[1]
                        current_cas[element[0]].append(element[1])

                    # 0->[0-15] 1->[0-14] 2->[0-1] 
                    for i in range(len(hzd_traits)):
                        for j in range(len(hzd_traits[i][0])):
                            row = hzd_traits[i][1][j]-1 #convert to pythonic indexing here
                            #print hzd_traits[i][0][j]
                            
                            hazard_subtraits = {}
                            for sub in hzd_sub_traits:
                                col = excel_col_to_num(sub[1])
                                val = sheet.cell_value(row,col)
                                if isinstance(val, unicode):
                                    val = val.replace(u'\xf6', u'')
                                    val = val.replace(u'\xba', u'')

                                hazard_subtraits[sub[0]] = [val]
                                
                                if sub[0] == "hazard_name":
                                    current_cas['hazards'][hzd_traits[i][0][j]][sub[0]].append(hzd_traits[i][0][j])
                                else:
                                    current_cas['hazards'][hzd_traits[i][0][j]][sub[0]].append(val)
                
                ## This section is used if it is a new CAS (this should be the case for all imports anyways)
                else:
                    cas_no_ind.append(cas_no_check)
                    
                    for element in absolute_pos_fields:
                        if element[0] == 'cas_no':
                          cas_no = sheet.cell_value(element[1]-1,excel_col_to_num(element[2]));

                        data[element[0]] = [sheet.cell_value(element[1]-1,excel_col_to_num(element[2]))]

                    for element in calculated_fields:
                        data[element[0]] = [element[1]]

                    # 0->[0-15] 1->[0-14] 2->[0-1] 
                    for i in range(len(hzd_traits)):
                        for j in range(len(hzd_traits[i][0])):
                            row = hzd_traits[i][1][j]-1 #convert to pythonic indexing here
                            
                            hazard_subtraits = {}
                            for sub in hzd_sub_traits:
                                col = excel_col_to_num(sub[1])
                                val = sheet.cell_value(row,col)
                                if isinstance(val, unicode):
                                    val = val.replace(u'\xf6', u'')
                                    val = val.replace(u'\xba', u'')

                                hazard_subtraits[sub[0]] = [val]
                                if sub[0] == "hazard_name":
                                    hazard_subtraits[sub[0]] = [hzd_traits[i][0][j]]
                                else:
                                    hazard_subtraits[sub[0]] = [val]

                            hazard_traits[hzd_traits[i][0][j]] = hazard_subtraits

                    data['hazards'] = hazard_traits
                    total_data[cas_no] = data

        ## Kept this print statement to show how data can be accessed after converting to JSON
        #print json.dumps(total_data['6-85-2']['hazards']['explosives'], indent=2)
        return total_data

    
## Translator Functions
#
# This function imports data from the Japan excel files into a GHS JSON format that will be used later 
# to translate to a greenscreen JSON format
#
#def import_ghs_japan_json(ghs_data_files, data_dir):



#Translate ghs_japan_json to gs
def translate_ghs_japan_json(json_data):
    print('Translating GHS Japan JSON data to Green Screen Hazard Rating...')

    criteria_1 = {}
    criteria_1['Category 1A'] = 4
    criteria_1['Category 1B'] = 4
    criteria_1['Category 2'] = 3
    criteria_1['Not classified'] = 2

    criteria_2 = {}
    criteria_2['Category 1'] = 5
    criteria_2['Category 2'] = 5
    criteria_2['Category 3'] = 4
    criteria_2['Category 4'] = 3
    criteria_2['Category 5'] = 2
    criteria_2['Not classified'] = 2

    criteria_3 = {}
    criteria_3['Category 1'] = 5
    criteria_3['Category 2'] = 4
    criteria_3['Category 3'] = 3
    criteria_3['Not classified'] = 2

    criteria_4 = {}
    criteria_4['Category 1'] = 4
    criteria_4['Category 2'] = 3
    criteria_4['Not classified'] = 2

    ## There's a typo in one of the CAS materials (Category1), it is treated as 1A since that's the highest
    criteria_5 = {}
    criteria_5['Category 1A'] = 4
    criteria_5['Category 1B'] = 3
    criteria_5['Not classified'] = 2
    criteria_5['Category1'] = 4

    criteria_6 = {}
    criteria_6['Category 1'] = 5
    criteria_6['Category 2A'] = 4
    criteria_6['Category 2B'] = 3
    criteria_6['Not classified'] = 2  

    criteria_7 = {}
    criteria_7['Category 4'] = 3  

    criteria_8 = {}
    criteria_8['Not classified'] = 2  

    criteria_9 = {}
    criteria_9['Category 1'] = 3 
    criteria_9['Not classified'] = 2 

    criteria_10 = {}
    criteria_10['Category 1'] = 5
    criteria_10['Category 2'] = 4
    criteria_10['Category 3'] = 3
    criteria_10['Category 4'] = 3
    criteria_10['Not classified'] = 2

    criteria_11 = {}
    criteria_11['Category 1'] = 4 
    criteria_11['Not classified'] = 2 

    criteria_12 = {}
    criteria_12['Category 1'] = 4
    criteria_12['Category 2'] = 3
    criteria_12['Category A'] = 3
    criteria_12['Category B'] = 2
    criteria_12['Not classified'] = 2

    criteria_13 = {}
    criteria_13['Category 1'] = 4
    criteria_13['Category 2'] = 3
    criteria_13['Category 3'] = 2
    criteria_13['Not classified'] = 2

    bench_numbers = {}
    bench_numbers['1'] = 0
    bench_numbers['2'] = 0
    bench_numbers['3'] = 0
    bench_numbers['4'] = 0
    bench_numbers['U'] = 0

    total_data = {}

    for CAS in json_data:
        ## cas_data holds all the data for this specific CAS material
        cas_data = {}
        cas_data['!warning'] = []

        ## The Japan GHS has some entries with empty CAS numbers, we ignore these
        if CAS is "":
            print( "Empty CAS number with ID: " )
            print( json_data[CAS]['ID'] )
            pass

        else:
            try:
                ## Make sure that the CAS number fits into CAS guidelines
                validated = validate_CAS(CAS)    

                if validated:
                    pass

                else: 
                    ## In the case of an invalid CAS number, a warning is added but the CAS is still treated as normal
                    ## However there is an option to just ignore the CAS entirely by raising the InvalidCAS_Error
                    # raise InvalidCAS_Error
                    cas_data['!warning'].append('This is an invalid CAS number. Please check your formatting (extra spaces, etc.) and numbers.')

                cas_data['cas_no'] = json_data[CAS]['cas_no'][0]
                cas_data['descriptive_name'] = [json_data[CAS]['descriptive_name'][0]]

                ## Can remove Japana GHS ID from real GS later, useful for easy matching to Japan excel data
                cas_data['ID'] = json_data[CAS]['ID'][0]

                for hazard in json_data[CAS]['hazards']:
                    cas_data['multiple_test'] = jsonify_hazard(json_data, cas_data, 'AA', CAS, hazard, 'Ecotoxicity', criteria_3)
 
                    ## Found multiple sources if jsonify_hazard returned a 1
                    if cas_data['multiple_test'] == 1:
                        raise MultipleSource_Error
                    ## Else we can ignore this test and delete it
                    else:
                        del cas_data['multiple_test']
                    
                    ## Acute aquatic toxicity
                    if hazard == "acute_aquatic_toxicity":
                        cas_data['AA'] = jsonify_hazard(json_data, cas_data, 'AA', CAS, hazard, 'Ecotoxicity', criteria_3)

                        ##Final hazard rating created here, if there is a previous GS JSON then we'll need to append instead
                        ##for now, we will declare hazard rating
                        cas_data['AA']['hazard_rating'] = []
                        
                        for x in range(0, len(cas_data['AA']['hazard_rating_temp'])):
                            try:     
                                rating = int(cas_data['AA']['hazard_rating_temp'][x])
                            except ValueError:
                                rating = int(cas_data['AA']['hazard_rating_temp'][x][2])

                            cas_data['AA']['hazard_rating'].append(rating)
                        
                        del cas_data['AA']['hazard_rating_temp']
                        cas_data['AA']['overall_hazard_rating'] = max(cas_data['AA']['hazard_rating'])

                    ## Acute Mammalian Toxicity
                    elif hazard == "acute_toxicity_oral":
                        cas_data['AT'] = jsonify_hazard(json_data, cas_data, 'AT', CAS, hazard, 'Group II and II* Human', criteria_2)

                    elif hazard == "acute_toxicity_dermal":
                        cas_data['AT'] = jsonify_hazard(json_data, cas_data, 'AT', CAS, hazard, 'Group II and II* Human', criteria_2)

                    elif hazard == "acute_toxicity_inhalation_gas":
                        cas_data['AT'] = jsonify_hazard(json_data, cas_data, 'AT', CAS, hazard, 'Group II and II* Human', criteria_2)

                    elif hazard == "acute_toxicity_inhalation_vapor":
                        cas_data['AT'] = jsonify_hazard(json_data, cas_data, 'AT', CAS, hazard, 'Group II and II* Human', criteria_2)

                    elif hazard == "acute_toxicity_inhalation_dust":
                        cas_data['AT'] = jsonify_hazard(json_data, cas_data, 'AT', CAS, hazard, 'Group II and II* Human', criteria_2)

                    ## Carcinogenicity
                    elif hazard == "carcinogenicity":
                        cas_data['C'] = jsonify_hazard(json_data, cas_data, 'C', CAS, hazard, 'Group I', criteria_1)

                        cas_data['C']['hazard_rating'] = []
                        
                        for x in range(0, len(cas_data['C']['hazard_rating_temp'])):
                            try:     
                                rating = int(cas_data['C']['hazard_rating_temp'][x])
                            except ValueError:
                                rating = int(cas_data['C']['hazard_rating_temp'][x][2])

                            cas_data['C']['hazard_rating'].append(rating)
                        
                        del cas_data['C']['hazard_rating_temp']
                        cas_data['C']['overall_hazard_rating'] = max(cas_data['C']['hazard_rating'])

                    ## Chronic Aquatic Toxicity
                    elif hazard == "chronic_aquatic_toxicity":
                        cas_data['CA'] = jsonify_hazard(json_data, cas_data, 'CA', CAS, hazard, 'Ecotoxicity', criteria_7)

                        cas_data['CA']['hazard_rating'] = []
                        
                        for x in range(0, len(cas_data['CA']['hazard_rating_temp'])):
                            try:     
                                rating = int(cas_data['CA']['hazard_rating_temp'][x])
                            except ValueError:
                                rating = int(cas_data['CA']['hazard_rating_temp'][x][2])

                            cas_data['CA']['hazard_rating'].append(rating)
                        
                        del cas_data['CA']['hazard_rating_temp']
                        cas_data['CA']['overall_hazard_rating'] = max(cas_data['CA']['hazard_rating'])

                    ## Developmental or Reproductive
                    elif hazard == "toxic_to_reproduction":
                        cas_data['D'] = jsonify_hazard(json_data, cas_data, 'D', CAS, hazard, 'Group I', criteria_1)
         
                        cas_data['D']['hazard_rating'] = []

                        for x in range(0, len(cas_data['D']['hazard_rating_temp'])):
                            try:     
                                rating = int(cas_data['D']['hazard_rating_temp'][x])
                            except ValueError:
                                rating = int(cas_data['D']['hazard_rating_temp'][x][2])

                            cas_data['D']['hazard_rating'].append(rating)
                        
                        del cas_data['D']['hazard_rating_temp']
                        cas_data['D']['overall_hazard_rating'] = max(cas_data['D']['hazard_rating'])

                        cas_data['R'] = jsonify_hazard(json_data, cas_data, 'R', CAS, hazard, 'Group I', criteria_1)

                        cas_data['R']['hazard_rating'] = []

                        for x in range(0, len(cas_data['R']['hazard_rating_temp'])):
                            try:     
                                rating = int(cas_data['R']['hazard_rating_temp'][x])
                            except ValueError:
                                rating = int(cas_data['R']['hazard_rating_temp'][x][2])

                            cas_data['R']['hazard_rating'].append(rating)
                        
                        del cas_data['R']['hazard_rating_temp']
                        cas_data['R']['overall_hazard_rating'] = max(cas_data['R']['hazard_rating'])

                    ## Flammability
                    elif hazard == "flammable_liquids":
                        cas_data['F'] = jsonify_hazard(json_data, cas_data, 'F', CAS, hazard, 'flammability', criteria_10)
                        
                    elif hazard == "flammable_gases":
                        cas_data['F'] = jsonify_hazard(json_data, cas_data, 'F', CAS, hazard, 'flammability', criteria_12)

                    elif hazard == "flammable_solids":
                        cas_data['F'] = jsonify_hazard(json_data, cas_data, 'F', CAS, hazard, 'flammability', criteria_4)
                        
                    elif hazard == "flammable_aerosols":
                        cas_data['F'] = jsonify_hazard(json_data, cas_data, 'F', CAS, hazard, 'flammability', criteria_13)

                    elif hazard == "pyrophoric_liquids":
                        cas_data['F'] = jsonify_hazard(json_data, cas_data, 'F', CAS, hazard, 'flammability', criteria_11)
                        
                    elif hazard == "pyrophoric_solids":
                        cas_data['F'] = jsonify_hazard(json_data, cas_data, 'F', CAS, hazard, 'flammability', criteria_11)

                    ## Eye Irritation
                    elif hazard == "serious_eye_damage_irritation":

                        cas_data['IrE'] = jsonify_hazard(json_data, cas_data, 'IrE', CAS, hazard, 'Group II & II*', criteria_6)
                      
                        cas_data['IrE']['hazard_rating'] = []
                        
                        for x in range(0, len(cas_data['IrE']['hazard_rating_temp'])):
                            try:     
                                rating = int(cas_data['IrE']['hazard_rating_temp'][x])
                            except ValueError:
                                rating = int(cas_data['IrE']['hazard_rating_temp'][x][2])

                            cas_data['IrE']['hazard_rating'].append(rating)
                        
                        del cas_data['IrE']['hazard_rating_temp']
                        cas_data['IrE']['overall_hazard_rating'] = max(cas_data['IrE']['hazard_rating'])

                    ## Skin Irritation
                    elif hazard == "skin_corrosion_irritation":
                        cas_data['IrS'] = jsonify_hazard(json_data, cas_data, 'IrS', CAS, hazard, 'Group II & II*', criteria_3)

                        cas_data['IrS']['hazard_rating'] = []
                        
                        for x in range(0, len(cas_data['IrS']['hazard_rating_temp'])):
                            try:     
                                rating = int(cas_data['IrS']['hazard_rating_temp'][x])
                            except ValueError:
                                rating = int(cas_data['IrS']['hazard_rating_temp'][x][2])

                            cas_data['IrS']['hazard_rating'].append(rating)
                        
                        del cas_data['IrS']['hazard_rating_temp']
                        cas_data['IrS']['overall_hazard_rating'] = max(cas_data['IrS']['hazard_rating'])

                    ## Mutagenicity/Genotoxicity
                    elif hazard == "germ_cell_mutagenicity":
                        cas_data['M'] = jsonify_hazard(json_data, cas_data, 'M', CAS, hazard, 'Group I', criteria_1)
                        
                        cas_data['M']['hazard_rating'] = []
                        
                        for x in range(0, len(cas_data['M']['hazard_rating_temp'])):
                            try:     
                                rating = int(cas_data['M']['hazard_rating_temp'][x])
                            except ValueError:
                                rating = int(cas_data['M']['hazard_rating_temp'][x][2])

                            cas_data['M']['hazard_rating'].append(rating)
                        
                        del cas_data['M']['hazard_rating_temp']
                        cas_data['M']['overall_hazard_rating'] = max(cas_data['M']['hazard_rating'])

                    ## Neurotoxicity and Systemic Toxicity are in one entry for the Japan database, they're separated by keywords
                    ## The keywords are not guaranteed to cover all of the ones used in the data, if some are missing please report it
                    
                    ## Single Exposure
                    elif hazard == "systemic_toxicity_single_exposure":
                        cas_data['N_s'] = jsonify_hazard(json_data, cas_data, 'N_s', CAS, hazard, 'Group II & II*', criteria_3)

                        cas_data['N_s']['hazard_rating'] = []
                        
                        for x in range(0, len(cas_data['N_s']['hazard_rating_temp'])):
                            try:     
                                rating = int(cas_data['N_s']['hazard_rating_temp'][x])
                            except ValueError:
                                rating = int(cas_data['N_s']['hazard_rating_temp'][x][2])

                            cas_data['N_s']['hazard_rating'].append(rating)
                        
                        del cas_data['N_s']['hazard_rating_temp']
                        cas_data['N_s']['overall_hazard_rating'] = max(cas_data['N_s']['hazard_rating'])


                        cas_data['ST_s'] = jsonify_hazard(json_data, cas_data, 'ST_s', CAS, hazard, 'Group II & II*', criteria_3)

                        cas_data['ST_s']['hazard_rating'] = []
                        
                        for x in range(0, len(cas_data['ST_s']['hazard_rating_temp'])):
                            try:     
                                rating = int(cas_data['ST_s']['hazard_rating_temp'][x])
                            except ValueError:
                                rating = int(cas_data['ST_s']['hazard_rating_temp'][x][2])

                            cas_data['ST_s']['hazard_rating'].append(rating)
                        
                        del cas_data['ST_s']['hazard_rating_temp']
                        cas_data['ST_s']['overall_hazard_rating'] = max(cas_data['ST_s']['hazard_rating'])

                    ## Repeat Exposure
                    elif hazard == "systemic_toxicity_repeat_exposure":
                        cas_data['N_r'] = jsonify_hazard(json_data, cas_data, 'N_r', CAS, hazard, 'Group II & II*', criteria_4)

                        cas_data['N_r']['hazard_rating'] = []
                        
                        for x in range(0, len(cas_data['N_r']['hazard_rating_temp'])):
                            try:     
                                rating = int(cas_data['N_r']['hazard_rating_temp'][x])
                            except ValueError:
                                rating = int(cas_data['N_r']['hazard_rating_temp'][x][2])

                            cas_data['N_r']['hazard_rating'].append(rating)
                        
                        del cas_data['N_r']['hazard_rating_temp']
                        cas_data['N_r']['overall_hazard_rating'] = max(cas_data['N_r']['hazard_rating'])

                        cas_data['ST_r'] = jsonify_hazard(json_data, cas_data, 'ST_r', CAS, hazard, 'Group II & II*', criteria_4)

                        cas_data['ST_r']['hazard_rating'] = []
                        
                        for x in range(0, len(cas_data['ST_r']['hazard_rating_temp'])):
                            try:     
                                rating = int(cas_data['ST_r']['hazard_rating_temp'][x])
                            except ValueError:
                                rating = int(cas_data['ST_r']['hazard_rating_temp'][x][2])

                            cas_data['ST_r']['hazard_rating'].append(rating)
                        
                        del cas_data['ST_r']['hazard_rating_temp']
                        cas_data['ST_r']['overall_hazard_rating'] = max(cas_data['ST_r']['hazard_rating'])
                   
                    ## Reactivity     
                    elif hazard == "explosives":
                        cas_data['Rx'] = jsonify_hazard(json_data, cas_data, 'Rx', CAS, hazard, 'Physical', criteria_8)

                    elif hazard == "self_reactive_substances":
                        cas_data['Rx'] = jsonify_hazard(json_data, cas_data, 'Rx', CAS, hazard, 'Physical', criteria_8)
                        
                    elif hazard == "substances_mixtures_emit_flammable_gas_in_contact_with_water":
                        cas_data['Rx'] = jsonify_hazard(json_data, cas_data, 'Rx', CAS, hazard, 'Physical', criteria_3)

                    elif hazard == "oxidizing_gases":
                        cas_data['Rx'] = jsonify_hazard(json_data, cas_data, 'Rx', CAS, hazard, 'Physical', criteria_11)

                    elif hazard == "oxidizing_liquids":
                        cas_data['Rx'] = jsonify_hazard(json_data, cas_data, 'Rx', CAS, hazard, 'Physical', criteria_3)

                    elif hazard == "oxidizing_solids":
                        cas_data['Rx'] = jsonify_hazard(json_data, cas_data, 'Rx', CAS, hazard, 'Physical', criteria_3)

                    elif hazard == "organic_peroxides":
                        cas_data['Rx'] = jsonify_hazard(json_data, cas_data, 'Rx', CAS, hazard, 'Physical', criteria_8)
                        
                    elif hazard == "self_heating_substances":
                        cas_data['Rx'] = jsonify_hazard(json_data, cas_data, 'Rx', CAS, hazard, 'Physical', criteria_4)

                    elif hazard == "corrosive_to_metals":
                        cas_data['Rx'] = jsonify_hazard(json_data, cas_data, 'Rx', CAS, hazard, 'Physical', criteria_9)

                    ## Respiratory Sensitization/Skin Sensitization, Japan fits these two hazards into one on their excel sheet
                    elif hazard == "respiratory_skin_sensitizer":
                        cas_data['SnR'] = jsonify_hazard(json_data, cas_data, 'SnR', CAS, hazard, 'Group II & II*', criteria_5)

                        cas_data['SnR']['hazard_rating'] = []
                        
                        for x in range(0, len(cas_data['SnR']['hazard_rating_temp'])):
                            try:     
                                rating = int(cas_data['SnR']['hazard_rating_temp'][x])
                            except ValueError:
                                rating = int(cas_data['SnR']['hazard_rating_temp'][x][2])

                            cas_data['SnR']['hazard_rating'].append(rating)
                        
                        del cas_data['SnR']['hazard_rating_temp']
                        cas_data['SnR']['overall_hazard_rating'] = max(cas_data['SnR']['hazard_rating'])
                        
                        cas_data['SnS'] = jsonify_hazard(json_data, cas_data, 'SnS', CAS, hazard, 'Group II & II*', criteria_5)

                        cas_data['SnS']['hazard_rating'] = []
                        
                        for x in range(0, len(cas_data['SnS']['hazard_rating_temp'])):
                            try:     
                                rating = int(cas_data['SnS']['hazard_rating_temp'][x])
                            except ValueError:
                                rating = int(cas_data['SnS']['hazard_rating_temp'][x][2])

                            cas_data['SnS']['hazard_rating'].append(rating)
                        
                        del cas_data['SnS']['hazard_rating_temp']
                        cas_data['SnS']['overall_hazard_rating'] = max(cas_data['SnS']['hazard_rating'])

                ## This section is needed for the CAS hazards with multiple sources from Japan. 
                ## For example, Japan has 5 different ratings that all correspond to Acute Mammalian Toxicity

                ## This section has also been modified to work for multiple sources but since they're labelled 
                ## as errors we will never need the extra functionality

                cas_data['AT']['hazard_rating'] = []
                cas_data['AT']['hazard_rating_1'] = []
                cas_data['AT']['hazard_rating_2'] = []

                for x in range(0, len(cas_data['AT']['hazard_rating_temp'])):
                    try:     
                        rating_1 = int(cas_data['AT']['hazard_rating_temp'][x])
                        cas_data['AT']['hazard_rating_1'].append(rating_1)
                    except ValueError:
                        rating_2 = int(cas_data['AT']['hazard_rating_temp'][x][2])
                        cas_data['AT']['hazard_rating_2'].append(rating_2)

                rating_3 = max(cas_data['AT']['hazard_rating_1'])
                cas_data['AT']['hazard_rating'].append(rating_3)

                rating_4 = cas_data['AT']['hazard_rating_2']
                if rating_4:
                    cas_data['AT']['hazard_rating'].append(max(rating_4))

                cas_data['AT']['overall_hazard_rating'] = max(cas_data['AT']['hazard_rating'])
            
                del cas_data['AT']['hazard_rating_temp']
                del cas_data['AT']['hazard_rating_1']
                del cas_data['AT']['hazard_rating_2']

                cas_data['F']['hazard_rating'] = []
                cas_data['F']['hazard_rating_1'] = []
                cas_data['F']['hazard_rating_2'] = []

                for x in range(0, len(cas_data['F']['hazard_rating_temp'])):
                    try:     
                        rating_1 = int(cas_data['F']['hazard_rating_temp'][x])
                        cas_data['F']['hazard_rating_1'].append(rating_1)
                    except ValueError:
                        rating_2 = int(cas_data['F']['hazard_rating_temp'][x][2])
                        cas_data['F']['hazard_rating_2'].append(rating_2)

                rating_3 = max(cas_data['F']['hazard_rating_1'])
                cas_data['F']['hazard_rating'].append(rating_3)

                rating_4 = cas_data['F']['hazard_rating_2']
                if rating_4:
                    cas_data['F']['hazard_rating'].append(max(rating_4))

                cas_data['F']['overall_hazard_rating'] = max(cas_data['F']['hazard_rating'])
            
                del cas_data['F']['hazard_rating_temp']
                del cas_data['F']['hazard_rating_1']
                del cas_data['F']['hazard_rating_2'] 

                cas_data['Rx']['hazard_rating'] = []
                cas_data['Rx']['hazard_rating_1'] = []
                cas_data['Rx']['hazard_rating_2'] = []

                for x in range(0, len(cas_data['Rx']['hazard_rating_temp'])):
                    try:     
                        rating_1 = int(cas_data['Rx']['hazard_rating_temp'][x])
                        cas_data['Rx']['hazard_rating_1'].append(rating_1)
                    except ValueError:
                        rating_2 = int(cas_data['Rx']['hazard_rating_temp'][x][2])
                        cas_data['Rx']['hazard_rating_2'].append(rating_2)

                rating_3 = max(cas_data['Rx']['hazard_rating_1'])
                cas_data['Rx']['hazard_rating'].append(rating_3)

                rating_4 = cas_data['Rx']['hazard_rating_2']
                if rating_4:
                    cas_data['Rx']['hazard_rating'].append(max(rating_4))

                cas_data['Rx']['overall_hazard_rating'] = max(cas_data['Rx']['hazard_rating'])
            
                del cas_data['Rx']['hazard_rating_temp']
                del cas_data['Rx']['hazard_rating_1']
                del cas_data['Rx']['hazard_rating_2']  

                total_data[json_data[CAS]['cas_no'][0]] = cas_data

            except InvalidCAS_Error:
                print("Invalid CAS.")

            except MultipleSource_Error:
                print("Multiple Sources with CAS: " + CAS)

    return total_data


#
# CAS Validation has two steps: 
# Step 1: Verify that the number is formatted correctly (2-7 digits)-(1-2 digits)-(1 check sum digit)
# Step 2: Verify that the check sum is the correct amount when compared to the remainder of the rest of
# the numbers combined and multiplied according to the CAS validation system
#
def validate_CAS(CAS):
    try:
        ## Regular Expression used to easy number format validation
        m_obj = re.match(r"(\d{2,7}-\d{1,2}-\d$)", CAS)
        m_obj.group(0)

        new_CAS = CAS.replace("-","")
        check_CAS = CAS[-1]
        new_CAS = new_CAS[:-1]
        new_CAS = new_CAS[::-1]

        total_valid_value = 0
        for x in range(0,len(new_CAS)):
            valid_value = int(new_CAS[x]) * (x+1)
            total_valid_value += valid_value

        if total_valid_value%(10) == int(check_CAS):
            pass
        else:
            print("Invalid CAS: " + CAS)
            return 0
        return 1

    ## AttributeError raised if the regex does not find the correct format
    except AttributeError:
        ## A special case to this exception is when there are multiple CAS numbers in 1 file, 
        ## This section splits the CAS numbers and checks them individually
        m_CAS = CAS.replace(" ","")

        ## If multiple CAS numbers are found:
        if len(m_CAS.split(',')) > 1:
            ## m_string is a list of separated CAS numbers
            m_string = m_CAS.split(',')
            for lil_string in m_string:
                new_lil_string = lil_string.replace("-","")
                check_lil_string = lil_string[-1]
                new_lil_string = new_lil_string[:-1]
                ## Reverses the numbers
                new_lil_string = new_lil_string[::-1]

                total_valid_value = 0
                for x in range(0,len(new_lil_string)):
                    valid_value = int(new_lil_string[x]) * (x+1)
                    total_valid_value += valid_value

                if total_valid_value%(10) == int(check_lil_string):
                    pass

                else:
                    print("Invalid CAS: " + CAS)
                    return 0
            return 1

        else:
            print("Invalid CAS: " + CAS)
    return 0


#
# Will find max rating and update benchmark scores, includes trumping criteria
#
def gs_assessment_json(json_data):
    bench_numbers = {}
    bench_numbers['1'] = 0
    bench_numbers['2'] = 0
    bench_numbers['3'] = 0
    bench_numbers['4'] = 0
    bench_numbers['U'] = 0

    for CAS in json_data:
        json_data[CAS]['AA']['overall_hazard_rating'] = trumping(json_data[CAS]['AA']['list_rating'],json_data[CAS]['AA']['hazard_rating'])
        json_data[CAS]['AT']['overall_hazard_rating'] = trumping(json_data[CAS]['AT']['list_rating'],json_data[CAS]['AT']['hazard_rating'])
        json_data[CAS]['C']['overall_hazard_rating'] = trumping(json_data[CAS]['C']['list_rating'],json_data[CAS]['C']['hazard_rating'])
        json_data[CAS]['CA']['overall_hazard_rating'] = trumping(json_data[CAS]['CA']['list_rating'],json_data[CAS]['CA']['hazard_rating'])
        json_data[CAS]['D']['overall_hazard_rating'] = trumping(json_data[CAS]['D']['list_rating'],json_data[CAS]['D']['hazard_rating'])
        json_data[CAS]['F']['overall_hazard_rating'] = trumping(json_data[CAS]['F']['list_rating'],json_data[CAS]['F']['hazard_rating'])
        json_data[CAS]['IrE']['overall_hazard_rating'] = trumping(json_data[CAS]['IrE']['list_rating'],json_data[CAS]['IrE']['hazard_rating'])
        json_data[CAS]['IrS']['overall_hazard_rating'] = trumping(json_data[CAS]['IrS']['list_rating'],json_data[CAS]['IrS']['hazard_rating'])
        json_data[CAS]['M']['overall_hazard_rating'] = trumping(json_data[CAS]['M']['list_rating'],json_data[CAS]['M']['hazard_rating'])
        json_data[CAS]['N_r']['overall_hazard_rating'] = trumping(json_data[CAS]['N_r']['list_rating'],json_data[CAS]['N_r']['hazard_rating'])
        json_data[CAS]['N_s']['overall_hazard_rating'] = trumping(json_data[CAS]['N_s']['list_rating'],json_data[CAS]['N_s']['hazard_rating'])
        json_data[CAS]['R']['overall_hazard_rating'] = trumping(json_data[CAS]['R']['list_rating'],json_data[CAS]['R']['hazard_rating'])
        json_data[CAS]['Rx']['overall_hazard_rating'] = trumping(json_data[CAS]['Rx']['list_rating'],json_data[CAS]['Rx']['hazard_rating'])
        json_data[CAS]['ST_r']['overall_hazard_rating'] = trumping(json_data[CAS]['ST_r']['list_rating'],json_data[CAS]['ST_r']['hazard_rating'])
        json_data[CAS]['ST_s']['overall_hazard_rating'] = trumping(json_data[CAS]['ST_s']['list_rating'],json_data[CAS]['ST_s']['hazard_rating'])
        json_data[CAS]['SnR']['overall_hazard_rating'] = trumping(json_data[CAS]['SnR']['list_rating'],json_data[CAS]['SnR']['hazard_rating'])
        json_data[CAS]['SnS']['overall_hazard_rating'] = trumping(json_data[CAS]['SnS']['list_rating'],json_data[CAS]['SnS']['hazard_rating'])

        AA = json_data[CAS]['AA']['overall_hazard_rating']
        AT = json_data[CAS]['AT']['overall_hazard_rating']
        C = json_data[CAS]['C']['overall_hazard_rating']
        CA = json_data[CAS]['CA']['overall_hazard_rating']
        D = json_data[CAS]['D']['overall_hazard_rating']
        R = json_data[CAS]['R']['overall_hazard_rating']
        F = json_data[CAS]['F']['overall_hazard_rating']
        IrE = json_data[CAS]['IrE']['overall_hazard_rating']
        IrS = json_data[CAS]['IrS']['overall_hazard_rating']
        M = json_data[CAS]['M']['overall_hazard_rating']
        N_s = json_data[CAS]['N_s']['overall_hazard_rating']
        N_r = json_data[CAS]['N_r']['overall_hazard_rating']
        Rx = json_data[CAS]['Rx']['overall_hazard_rating']
        ST_s = json_data[CAS]['ST_s']['overall_hazard_rating']
        ST_r = json_data[CAS]['ST_r']['overall_hazard_rating']
        SnR = json_data[CAS]['SnR']['overall_hazard_rating']
        SnS = json_data[CAS]['SnS']['overall_hazard_rating']

        ## Endocrine, Persistence, Bioaccumulation data not available, defaults to 0
        E = 0
        P = 0
        B = 0

        ## Neurotoxicity
        N = max([N_r, N_s])

        ## Toxicity
        T = max([AT, ST_r, ST_s]) 

        ## Eco Toxicity
        eco_T = max([CA, AA])
        vHigh_T_B1 = max([T,eco_T])
        Group_1 = max([C,M,D,N,E])
        Group_2 = max([AT,ST_s,N_s, IrE, IrS])
        Group_2_star = max([ST_r,N_r,SnR,SnS]) #is Group 2* but cant use * so dos is used
        all_four_groups= max([eco_T,Group_1,Group_2,Group_2_star])

        ## Benchmark 1
        if (((P >= 4) and (B >= 4) 
            and ((max([eco_T, Group_2]) >=5) or (max([Group_1, Group_2_star]) >= 4))) #High P, B, (vHigh T or High T)
            or ((P >= 5) and (B >= 5)) #vHigh P, vHigh B
            or ((P >= 5) and ((max([eco_T, Group_2]) >=5) or (max([Group_1, Group_2_star]) >= 4))) #vHigh P, (vHigh T or High T)
            or ((B >= 5) and ((max([eco_T, Group_2]) >=5) or (max([Group_1, Group_2_star]) >= 4))) #vHigh B, (vHigh T or High T)
            or (Group_1 >= 4)): #Group I Human
            json_data[CAS]['gs_benchmark'] = 'Benchmark 1'
            bench_numbers['1'] += 1

        ## Benchmark 2 
        elif (((P >= 3) and (B >= 3) and (all_four_groups >= 3)) #Moderate P, B, T
              or ((P >= 4) and (B >= 4)) #High P, High B
              or ((P >= 4) and (all_four_groups >= 3)) #High B, Moderate T
              or ((B >= 4) and (all_four_groups >= 3)) #High B, Moderate T
              or (Group_1 >= 3) #moderate Moderate T (Group I Human)
              or ((max([eco_T, Group_2]) >= 5) or (Group_2_star >= 4)) #vHigh T (Eco_T or Group II) or High T (Group_2_star)
              or (F >= 4) #High F
              or (Rx >= 4)): #High Rx
            json_data[CAS]['gs_benchmark']= 'Benchmark 2' 
            bench_numbers['2'] += 1

        ## Benchmark 3
        elif ((P >= 3) #moderate P
               or (B >= 3) #moderate B 
               or (eco_T >= 3) #moderate eco_T
               or (max([Group_2, Group_2_star]) >= 3) #moderate T
               or (F >= 3)#moderate F
               or (Rx >= 3)):#moderate Rx
            json_data[CAS]['gs_benchmark'] = 'Benchmark 3'
            bench_numbers['3'] += 1

        ## Benchmark 4
        elif ((P <= 2) #low P
               and (B <= 2) #low B
               and (all_four_groups <= 2) #low four_groups
               and (F <= 2)
               and (Rx <= 2)
               and (B != 0)
               and (T != 0)
               and (eco_T != 0)): #moderate T
            json_data[CAS]['gs_benchmark'] = 'Benchmark 4'
            bench_numbers['4'] += 1

        else:
            json_data[CAS]['gs_benchmark']= 'Benchmark U'
            bench_numbers['U'] += 1

    print("Benchmark numbers: ")
    print("Benchmark 1:")
    print(bench_numbers['1'])
    print("Benchmark 2:")
    print(bench_numbers['2'])
    print("Benchmark 3:")
    print(bench_numbers['3'])
    print("Benchmark 4:")
    print(bench_numbers['4'])
    print("Benchmark U:")
    print(bench_numbers['U'])

    return json_data


def trumping(list_rating, ratings):
    try:
        return ratings[list_rating.index(4)]
    except ValueError:
        try:
            return ratings[list_rating.index(3)]
        except ValueError:
            try:
                return ratings[list_rating.index(2)]
            except ValueError:
                try:
                    return ratings[list_rating.index(1)]
                except ValueError:
                    return 0


def jsonify_hazard(json_data, cas_data, name, CAS, hazard, category, criteria):
    hazard_dict = {}
    class_num = 0
    hazard_dict['hazard_full_name'] = name
    hazard_dict['category'] = category

    ## This is to check if the hazard being accessed already exists for the case
    ## of multiple Japan hazards for one GS hazard (like acute mammalian toxicity), we pass in existing GS hazard data
    try: 
        if cas_data[name]:
            hazard_dict['hazard_rating_temp'] = cas_data[name]['hazard_rating_temp']
            append_flag = 0

    except KeyError:
        append_flag = 0

    ## If we run into a CAS material that has multiple sources then we return 1 which ends translation for this CAS
    if len(json_data[CAS]['hazards'][hazard]['classification']) > 1:
        return 1

    ## Should usually arrive here, this else section indicates that we have not run into duplicate sources
    ## while translating from the Japan GHS database
    else:
        systemic_words = (['respiratory', 'blood', 'kidney', 'liver', 'adrenal', 'gastro', 'systemic', 'eye', 
            'heart', 'bone', 'hematop', 'cardio', 'spleen', 'thyroid', 'lung', 'gingi', 'testes'])

        if append_flag:
            hazard_dict['date_imported'].append(time.ctime())
            hazard_dict['imported_by'].append(getpass.getuser())
            hazard_dict['date_classified'].append(json_data[CAS]['date_classified'][0])
            hazard_dict['source'].append('GHS Japan Country List')
            hazard_dict['list_type'].append('Screening A')
            hazard_dict['list_rating'].append(2)

        else:
            hazard_dict['date_imported'] = [time.ctime()]
            hazard_dict['imported_by'] = [getpass.getuser()]
            hazard_dict['date_classified'] = [json_data[CAS]['date_classified'][0]]
            hazard_dict['source'] = ['GHS Japan Country List']
            hazard_dict['list_type'] = ['Screening A']
            hazard_dict['list_rating'] = [2]

        try: 
            rating = 0

            ## ST_s or ST_r will set use_ST to 1 if it finds a rating, this is a special case where we do not
            ## use the normal rating method, instead the if statement with ST_s or ST_r will set the rating
            use_ST = 0


            try:
                ## Location is the variable name for the portion of the GHS data that has the classification for this hazard
                ## There are quite a few ways to find the location because of the different ways data is formatted


                ## Some system toxicity classifications have a different format without semi colons
                ## We must treat them as a special case
                no_semi = 0 

                ## There were a few problems with the format of the data in excel, since there were inconsistencies 
                ## the most common ones had to be accounted for here

                if json_data[CAS]['hazards'][hazard]['classification'][0].find(';') < 0:
                    no_semi = 1

                Sn_class = json_data[CAS]['hazards'][hazard]['classification'][0].split(';')

                if len(Sn_class) < 2:
                    ## Sometimes hazard classifications are not split by anything except a new line
                    Sn_class = json_data[CAS]['hazards'][hazard]['classification'][0].split('\n')

                    if len(Sn_class) < 2:
                        Sn_class = json_data[CAS]['hazards'][hazard]['classification'][0]
                        mid = Sn_class.find('Skin sensitizer')
                        part1 = Sn_class[0:mid]
                        part2 = Sn_class[mid:len(Sn_class)]
                        Sn_class = [part1,part2]
                        no_semi = 0

                    else:
                        no_semi = 0

                ## Sometimes hazard classifications are split by a comma
                if json_data[CAS]['hazards'][hazard]['classification'][0].find('),') >= 0:
                    no_semi = 1

                Sn_class_unsplit = json_data[CAS]['hazards'][hazard]['classification'][0]

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
                            print("IndexError, Sn_class is " )
                            print(Sn_class)
                            print("CAS: " + CAS)
                            print("Name: " + name)


                elif name == 'N_s':

                    if len(Sn_class) < 2 or no_semi == 1:
                        Sn_class = json_data[CAS]['hazards'][hazard]['classification'][0].split('),')
                        
                    for part in Sn_class:
                        found = part.find('nervous')
                        if found >= 0:
                            location = part
                            break

                        else:
                            location = 'No data available'


                elif name == 'N_r':
                    if len(Sn_class) < 2 or no_semi == 1:
                        Sn_class = json_data[CAS]['hazards'][hazard]['classification'][0].split('),')

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
                        Sn_class = json_data[CAS]['hazards'][hazard]['classification'][0].split('),')

                    for line in Sn_class:
                        for keyword in systemic_words:  
                            if line.find(keyword) >= 0:
                                for crit in criteria:        
                                    found = line.find(crit)
                                    if found >= 0:
                                        if criteria[crit] > max_rating:
                                            max_rating = criteria[crit]                

                    rating = max_rating
                    use_ST = 1
                            

                elif name == 'ST_r':
                    max_rating = 0
                    if len(Sn_class) < 2 or no_semi == 1:
                        Sn_class = json_data[CAS]['hazards'][hazard]['classification'][0].split('),')

                    for line in Sn_class:
                        for keyword in systemic_words:  
                            if line.find(keyword) >= 0:
                                for crit in criteria:        
                                    found = line.find(crit)
                                    if found >= 0:
                                        if criteria[crit] > max_rating:
                                            max_rating = criteria[crit] 

                    rating = max_rating
                    use_ST = 1

                ## The normal case where the hazard is not one of the six special cases
                else:
                    location = json_data[CAS]['hazards'][hazard]['classification'][0]


                ## This means we already have a rating and the current hazard is ST_s or ST_r
                if use_ST: 
                    pass

                else: 
                    ## Go through criteria and try to match to classification
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

    return hazard_dict


def save_xml_individual(xml_data, data_dir, list_type):
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
    etree.strip_attributes(xml_data, '{http://codespeak.net/lxml/objectify/pytype}pytype')
    if list_type == 'gs':
        print ('Saving Greenscreen xml data to ' + data_dir + '...')
        for i in range(len(xml_data.xpath('/root/gs_data'))):
            gs_str = 'gs_data['+str(i)+']'
            path = objectify.ObjectPath(['root', gs_str])
            var = path(xml_data)
            filename = str(var.cas_no) + '.xml'
            filepath = data_dir + '/' + filename
            FILE = open(filepath, 'w')
            FILE.writelines(etree.tostring(xml_data.gs_data[i], pretty_print=True))
            FILE.close() 
    if list_type == 'ghs':
        print('Saving GHS Japan xml data to ' + data_dir + '...')
        for i in range(len(xml_data.xpath('/root/ghs_data'))):
            gs_str = 'ghs_data['+str(i)+']'
            path = objectify.ObjectPath(['root', gs_str])
            var = path(xml_data)
            filename = str(var.cas_no) + '.xml'
            filepath = data_dir + '/' + filename
            FILE = open(filepath, 'w')
            FILE.writelines(etree.tostring(xml_data.ghs_data[i], pretty_print=True))
            FILE.close()
    print('Done.')
        

def save_xml_master(xml_data, data_dir, filename):
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
    etree.strip_attributes(xml_data, '{http://codespeak.net/lxml/objectify/pytype}pytype')
    print('Saving master xml data to ' + data_dir + '...')
    filepath = data_dir + '/' + filename
    FILE = open(filepath, 'w')
    FILE.writelines(etree.tostring(xml_data, pretty_print=True))
    FILE.close()
    print('Done.')


def save_json_individual(json_data, data_dir):
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

    print('Saving GHS Japan JSON data to ' + data_dir + '...')
        
    json_master = {}

    for item in json_data:    
        filename = item + '.json'
        filepath = data_dir + '/' + filename
        FILE = open(filepath, 'w')
        FILE.writelines(json.dumps(json_data[item], indent=2, sort_keys=True))
        FILE.close()

    print('Done.')


def save_json_individual_gs(json_data, data_dir):
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

    print('Saving GS Japan JSON data to ' + data_dir + '...')
        
    json_master = {}

    for item in json_data:    
        json_master[item] = json_data[item]['gs_benchmark']

        filename = item + '.json'
        filepath = data_dir + '/' + filename
        FILE = open(filepath, 'w')
        FILE.writelines(json.dumps(json_data[item], indent=2, sort_keys=True))
        FILE.close()

    filename = '1_master' + '.json'
    filepath = data_dir + '/' + filename
    FILE = open(filepath, 'w')
    FILE.writelines(json.dumps(json_master, indent=2, sort_keys=False))
    FILE.close()

    print('Done.')

def main():  
    ## Report time of code execution to check performance 
    #  Calls to time can be commented out or deleted. 
    t = time.time()

    ## Import the data: The download_files function requires that you
    #  know ahead of time the names of files to download.  If a website allows listing 
    #  of folder contents, the program could be extended to generate a list of file names 
    #  by download all content from a specified URL.
    url = 'http://www.safe.nite.go.jp/english/files/ghs_xls/'
    file_names = (['classification_result_e(ID001-100).xls',
                   'classification_result_e(ID101-200).xls',
                   'classification_result_e(ID201-300).xls',
                   'classification_result_e(ID301-400).xls',
                   'classification_result_e(ID401-500).xls',
                   'classification_result_e(ID501-600).xls',
                   'classification_result_e(ID601-700).xls',
                   'classification_result_e(ID701-800).xls',
                   'classification_result_e(ID801-900).xls',
                   'classification_result_e(ID901-1000).xls',
                   'classification_result_e(ID1001-1100).xls',
                   'classification_result_e(ID1101-1200).xls',
                   'classification_result_e(ID1201-1300).xls',
                   'classification_result_e(ID1301-1400).xls',
                   'classification_result_e(ID1401-1424).xls'])


    #  Specify where to save the data.
    #  If the directory does not exist, it will be created. 
    #  You may also skip this step and download data manually.
    data_dir = 'data/'

    #  Download the excel files from GHS Japan website. 
    download_files(url, data_dir, file_names)

    ## Import GHS Japan Data: This step converts the excel files to an lxml
    #  data structure. First we need to specify which file in the list is the 
    #  directory and which are the data files. This function was custom written
    #  around the format of the GHS_Japan Excel files. To import other databases
    #  it is necessary to develop additional import functions.

    ghs_japan_data_xml = import_ghs_japan(file_names, data_dir, file_type='xml')
    ghs_japan_data_json = import_ghs_japan(file_names, data_dir, file_type='json')

    ## Translate to Green Screen format.
    ## This function is also custom written for the ghs japan country list. Additional
    ## translation functions are necessary to translate from other libraries. 

    gs_japan_data_json = translate_ghs_japan_json(ghs_japan_data_json)

    ## Run the GS Japan JSON data through the assessment function to create GS benchmarks
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