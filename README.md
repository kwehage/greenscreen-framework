# Synopsis

This Python module consists of a collection of utilities for importing and
translating hazard data from publicly available Internet resources,
translating to an intermediate GreenScreen datastructure and computing an
overall GreenScreen benchmark score according to the GreenScreen for Safer
Chemicals methodology.

The entire benchmarking process, including the initial import of data,
translation to GreenScreen representation, and assessment of an overall
benchmark score, is completely computer automated. The resulting data is
exported in a JavaScript Object Notation (JSON) file format and is
suitable to be uploaded to a document storage system or relational
database for later retrieval.

At present, the module supports loading data from two hazard endpoint
data sources:

-   **Chemical Management Center**, part of a Japanese governmental organization
called the National Institute for Technology Evaluation. In the source code,
the dataset is referred to as the *GHS Japan country list* and is available
at the following url: <http://www.safe.nite.go.jp/english/ghs/ghs_index.html>.
According to the GreenScreen methodology, this list is classified as a
*Screening A* list.

-   **Proposition 65**, a list of chemicals known by the State of California to
have a 1 in 100,000 chance of causing cancer, birth defects or developmental
harm. The dataset is available at the following url:
<http://www.oehha.ca.gov/prop65/prop65_list/Newlist.html> According to the
GreenScreen methodology, this list is classified as an *Authoritative A* list.

## DISCLAIMER

The benchmark scores computed by this module do not constitute
comprehensive GreenScreen assessments. In addition to a benchmark score, a
comprehensive GreenScreen assessment contains a detailed report and
verification by a GreenScreen licensed profiler. Furthermore, a comprehensive
GreenScreen assessment is carried out on the basis of hazard endpoints spanning
most, if not all, of the eighteen categories described in the GreenScreen for
Safer chemicals methodology.

In this module's current state of development, a benchmark score is computed
only on the basis of data imported from the hazard endpoint data sources listed
above. Therefore, any benchmark scores computed by the module must be
considered *provisional* in nature, as appending additional hazard endpoint
data may result in a lower (more hazardous) overall benchmark score.

Nonetheless, the module is effective to identify
*Benchmark 1, Avoid: Chemical of High Concern* chemicals,
which, according the GreenScreen ListTranslator v1.2 method, are reported as
*LT-1: Benchmark 1* or *LT-P1: Possible Benchmark 1* scores, depending on
the source of the hazard endpoint that resulted in a provisional Benchmark 1
assessment. All other *provisional* scores are reported as *LT-U: Unspecified
Benchmark*.

## Recommendations for usage

Before using the module, it is recommended to register with the nonprofit
group, Clean Production Action, to receive specific details on performing
GreenScreen assessments and to familiarize yourself with the benchmarking
and translation process.
http://www.greenscreenchemicals.org/method/?/Greenscreen.php

As discussed above, as the results of the automated benchmarking process do not
constitute official, comprehensive assessments, the overall assessment should
be reported to a general audience as one of the following:

-   LT-1: Benchmark 1
-   LT-P1: Possible Benchmark 1
-   LT-U: Unspecified Benchmark

During the benchmarking process, a *provisional* benchmark score is computed
and stored in the data structure. The possible *provisional* benchmark scores
are listed below:

-   *Provisional* Benchmark 1, Avoid: Chemical of High Concern
-   *Provisional* Benchmark 2, Use: But Search for Safer Substitutes
-   *Provisional* Benchmark 3, Use: But Still Opportunity for Improvement
-   *Provisional* Benchmark 4, Prefer - Safer Chemical
-   *Provisional* Benchmark U, Unknown

The provisional scores should not be reported to a general audience, but
are recorded during the benchmarking process for their value to GreenScreen
practitioners. For example, once a licensed profiler deems that sufficient
hazard endpoint data has been appended for a given chemical and a
corresponding report has been generated, a provisional score *could* later be
reported as a comprehensive score.


# Installation

After cloning the project, install the Python module to your system path:

```bash
python setup.py install
```
A batch processing script is provided that will download data from the
GHS-Japan website, perform list translation and benchmarking. After
installing the Python module in the previous step, the
*greenscreen_batch_process* command line utility will be available and
can be executed by calling:

```bash
greenscreen_batch_process <data directory>
```
Replace ```<data directory>``` with the directory you wish to store the
information.

Alternatively, any of the functions contained within the module can be
reused in other Python applications.

The greenscreen_framework module class definitions can then be
used in other Python programs by putting the following at the top of
your Python script:

```python
import greenscreen_framework.greenscreen as gs
import greenscreen_framework.ghs as ghs
import greenscreen_framework.prop65 as prop65
```

Refer to the batch processing script *greenscreen_batch_process* for example
usage.


# Change Log
All notable changes to this project will be documented below.

## [1.0.1] - 2016-01-15
### Added
- prop65.py contains a Prop65 python class to load Proposition 65 data from
http://www.oehha.ca.gov/prop65/prop65_list/Newlist.html and translate/save the
results into an intermediate JSON file.

### Changed
- greenscreen.py added a method to load/merge Prop65 data that has been
translated/saved in an intermediate JSON format.
- README.md updated description of project

## [1.0.0] - 2015-07-08
### Added
- Initial commit

Copyright 2013-2016 Kristopher Wehage
