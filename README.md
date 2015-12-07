This program consists of a collection of utilities for importing and
processing hazard data from the Chemical Management Center, part of a
Japanese governmental organization called the National Institute for
Technology Evaluation. In the source code, the dataset is referred to
as the *GHS Japan country list* and is available at the following url: http://www.safe.nite.go.jp/english/ghs/ghs_index.html.

The code is used to automatically translate data to GreenScreen format
and perform a GreenScreen benchmark assessment. The translation from
GHS classification to GreenScreen hazard classification is performed
using the GreenScreen List Translator v1.2. The entire benchmarking process,
including the initial import of data from the GHS Japan country list,
translation to GreenScreen representation, and performing an overall
benchmark score, is completely computer automated. The resulting data is
exported in a JavaScript Object Notation (JSON) file format and is
suitable to be uploaded to a document storage system or relational
database for later retrieval.

Please register with the nonprofit group, Clean Production Action, to
receive specific details on the benchmarking and translation methodology.
http://www.greenscreenchemicals.org/method/?/Greenscreen.php


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

Copyright 2013-2015 Kristopher Wehage
University of California-Davis
