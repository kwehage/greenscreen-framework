#!/usr/bin/env python
'''
main.py
The 'main' python function illustrates how to combine the functions 
included in the greenscreen_tools module to:
* Specify URL, filenames and directory for downloading data 
* Create a new GHS Japan Data object
* Create a new GreenScreen Data object
* Translate GHS Japan Data object to GreenScreen Data object.
* Perform GreenScreen Benchmark assessment on GreenScreen Data object.

Copyright Kristopher Wehage, Panan Chenhansa, Julie M. Schoenung, 2013
University of California-Davis
This code comes with no warranties or guarantees of fitness for any purpose.
'''



import greenscreen_tools as gs
import time
import json
from lxml import etree

## Report time of code execution to check performance on your 
##  hardware. Calls to time can be commented out or deleted. 
t = time.time()

## Import the data: The download_files function requires that you
#  know ahead of time the names of files to download.  This code could  
#  be extended in a number of ways; for example, if a website allows listing 
#  of folder contents, the file_names list could be populated automatically based on
#  the listing to download all content from a specified URL.
#  The function could also be extended to access files by ftp, APIs, etc.
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
#  The data directory can be an absolute or relative path, 
#  Use only '/', no backslashes.
#  If the directory does not exist, it will be created. 
#  You can also skip this step and download data manually.
data_dir = 'data/'

#  Download the excel files from GHS Japan website. 
gs.download_files(url, data_dir, file_names)

## Import GHS Japan Data: This step converts the excel files to an lxml
#  data structure. First we need to specify which file in the list is the 
#  directory and which are the data files. This function was custom written
#  around the format of the GHS_Japan Excel files. To import other databases
#  it is necessary to develop additional import functions.

ghs_japan_data_xml = gs.import_ghs_japan(file_names, data_dir, file_type='xml')
ghs_japan_data_json = gs.import_ghs_japan(file_names, data_dir, file_type='json')

## Translate to Green Screen format.
## This function is also custom written for the ghs japan country list. Additional
## translation functions are necessary to translate from other libraries. 

gs_japan_data_json = gs.translate_ghs_japan_json(ghs_japan_data_json)

## Run the GS Japan JSON data through the assessment function to create GS benchmarks
gs_japan_data_json = gs.gs_assessment_json(gs_japan_data_json)

## Export GHS JSON data 
data_dir = 'data/ghs_json_data/'
gs.save_json_individual(ghs_japan_data_json, data_dir)

## Export GS JSON data
data_dir = 'data/gs_json_data/'
gs.save_json_individual_gs(gs_japan_data_json, data_dir)

## Export XML Data: 
data_dir = 'data/ghs_xml_data/'
gs.save_xml_individual(ghs_japan_data_xml, data_dir, 'ghs')
gs.save_xml_master(ghs_japan_data_xml, data_dir, 'ghs_master_list.xml')

elapsed = time.time() - t
print 'Time elapsed: ', elapsed, ' seconds.'
