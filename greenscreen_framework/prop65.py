#!/usr/bin/env python3

import time
import openpyxl
import json
import os
import re
import sys
from urllib.request import urlopen

'''
prop65.py

This module contains a Python class, 'Prop65Data', that is used
to import data from the Proposition 65 website and translate the hazards from
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


class InvalidProp65File_Error(Exception):
    pass


class Prop65Data(object):
    '''
    Prop65Data Python class
    '''
    def __init__(self, row, filename=None, file_path=None):
        '''
        Prop65Data Class constructor
        '''

        self.data = {'file_path': file_path}

        self.translation_criteria = {
            'C': {'name': 'Carcinogenicity',
                  'native_classification': [
                      'carcinogenicity']},

            'D': {'name': 'Developmental Hazard',
                  'native_classification': [
                      'reproductive_toxicity']},

            'R': {'name': 'Reproductive',
                  'native_classification': [
                      'reproductive_toxicity']}}

        if filename is None and row:
            result = self.import_data(row)
            if not result:
                self.data = None
            else:
                self.translate()

        elif filename:
            with open(filename, "r") as f:
                self.data = json.load(f)
            self.cas_number = self.data['cas_number']

        else:
            raise(InvalidProp65File_Error)

    def valid_cas(self):
        '''
        CAS Validation has two steps:
        Step 1: Verify that the number is formatted correctly (2-7 digits)-
                (1-2 digits)-(1 check sum digit)
        Step 2: Verify that the check sum is the correct amount when compared
                to the remainder of the rest of the numbers combined and
                multiplied according to the CAS validation system
        '''
        if not self.data['cas_number']:
            return False
        for cas in self.data['cas_number']:
            # Regular expression used to validate number format
            m_obj = re.match(r"(\d{2,7}-\d{1,2}-\d$)", cas)
            if not m_obj:
                return False
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

    def import_data(self, row):
        import_data = [cell.value for cell in row]
        print(import_data)
        if not import_data:
            return False
        if not import_data[0] or \
                'Delisted' in import_data[0] or \
                'Click here for the basis for' in import_data[0]:
            return False
        self.data['list_type'] = 'Authoritative A'
        self.data['list_rating'] = 4
        self.data['source'] = 'Proposition 65'
        self.data['descriptive_name'] = import_data[0]
        self.data['hazards'] = import_data[1]
        self.data['cas_number'] = import_data[3]
        self.data['date_imported'] = time.ctime()
        if self.data['cas_number']:
            self.data['cas_number'] = \
                self.data['cas_number'].replace(' ', '').replace(
                    '/', ',').replace(';', ',')
            self.data['ID'] = self.data['cas_number']
            self.data['cas_number'] = self.data['cas_number'].split(',')

        if not self.valid_cas():
            return False
        self.cas_number = self.data['cas_number']
        self.data['date_classified'] = '%d-%d-%d' % (
            import_data[4].year,
            import_data[4].month,
            import_data[4].day)
        self.data['date_imported'] = time.ctime()
        return True

    def translate(self):
        self.data['translated_data'] = {}
        if 'cancer' in self.data['hazards']:
            self.data['translated_data']['C'] = 4
        else:
            self.data['translated_data']['C'] = 0
        if 'developmental' in self.data['hazards']:
            self.data['translated_data']['D'] = 4
        else:
            self.data['translated_data']['D'] = 0
        if 'male' in self.data['hazards']:
            self.data['translated_data']['R'] = 4
        else:
            self.data['translated_data']['R'] = 0
        print(self.data['translated_data'])

    def save(self, filepath):
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        filename = self.data['ID'] + '.json'
        if os.path.exists(
                os.path.join(filepath, filename + '.json')):
            i = 2
            while True:
                filename = self.data['ID'] + '_%s.json' % i
                i += 1
                if not os.path.exists(os.path.join(filepath, filename)):
                    break
        with open(os.path.join(filepath, filename), "w") as f:
            print(os.path.join(filepath, filename))
            print(self.data)
            json.dump(self.data, f, indent=4, sort_keys=True)


def batch_process(
        excel_file_path,
        prop65_file_path,
        url='http://www.oehha.ca.gov/prop65/prop65_list/files/',
        file_list=['120415listlinked.xlsx']):
    if not os.path.exists(excel_file_path):
        os.makedirs(excel_file_path)
    if not os.path.exists(prop65_file_path):
        os.makedirs(prop65_file_path)
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
        sheet = openpyxl.load_workbook(filename=full_path).active

        for row in sheet.iter_rows('A%d:F2%d' % (15, 982)):
            prop65_data = Prop65Data(row)
            if prop65_data.data:
                prop65_data.save(prop65_file_path)

if __name__ == "__main__":
    t = time.time()
    excel_file_path = 'data'
    prop65_file_path = 'data/prop65_data'
    batch_process(excel_file_path, prop65_file_path)
    print('Time elapsed: %d seconds' % (time.time() - t))
