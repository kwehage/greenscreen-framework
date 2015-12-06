from distutils.core import setup

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
                'greenscreen_framework.prop65',
                'greenscreen_framework.greenscreen'],
    package_data={'package': "data/*"},
    scripts=['scripts/greenscreen_batch_process'],
    long_description="A collection of utilities for manipulating hazard " +
                     "data and performing Green Screen hazard assessments.")
