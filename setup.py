from distutils.core import setup

files = ["data/*"]

setup(name = "greenscreen_framework",
    version = "100",
    description = "A collection of utilities for manipulating hazard data and performing Green Screen hazard assessments.",
    author = "Kristopher Wehage",
    author_email = "ktwehage@ucdavis.edu",
    url = "http://amrl.engr.ucdavis.edu",
    packages = ['greenscreen_framework'],
    package_data = {'package' : files },
    long_description = """A collection of utilities for manipulating hazard data and performing Green Screen hazard assessments."""     
) 