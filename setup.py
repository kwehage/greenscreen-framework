from distutils.core import setup

files = ["data/*"]

setup(
    name="greenscreen_framework",
    version="1.0.0",
    description="A collection of utilities for manipulating hazard data " +
                "and performing Green Screen hazard assessments.",
    author="Kristopher Wehage",
    author_email="ktwehage@ucdavis.edu",
    url="http://amrl.engr.ucdavis.edu",
    packages=['greenscreen_framework'],
    py_modules=['greenscreen_framework.ghs',
                'greenscreen_framework.greenscreen'],
    package_data={'package': files},
    long_description="A collection of utilities for manipulating hazard " +
                     "data and performing Green Screen hazard assessments.")
