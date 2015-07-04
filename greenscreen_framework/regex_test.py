#!/usr/bin/env python

import re

if __name__ == "__main__":
    mystring = 'Category 2 (heart, liver, kidney), ' + \
               'Category 3 (nervous, liver, kidney)'
    # print(mystring)
    matcher = re.compile(r"[A-Za-z][A-Za-z1-9 ]*?\(.*?\)")
    result = matcher.findall(mystring)

    print(result)
