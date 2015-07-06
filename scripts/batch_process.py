#!/usr/bin/env python3

import greenscreen_framework
import time

'''
batch_process.py

This script demonstrates usage of the greenscreen_framework python module.

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

if __name__ == "__main__":
        t = time.time()
        excel_file_path = 'data'
        ghs_japan_file_path = 'data/ghs_json_data'
        greenscreen_file_path = 'data/greenscreen_data'
        greenscreen_framework.ghs.batch_process(
            excel_file_path, ghs_japan_file_path)
        greenscreen_framework.greenscreen.bulk_ghs_japan_import(
            ghs_japan_file_path, greenscreen_file_path)
        print('Time elapsed: %d seconds' % (time.time() - t))
