"""
What Should I need to write in __init__.py actually?

pyracinghk: A Hong Kong Racing Information package for Python
================================================
pyracinghk imports all the functions from:
 BeautifulSoup4
 NumPy
 Pandas

 ...
and in addition provides:
Subpackages
-----------
Using any of these subpackages requires an explicit import.  For example,
 import pyracinghk.horse
::
 horse
 
"""


from __future__ import division 
from __future__ import print_function
from __future__ import absolute_import
from __future__ import six

from bs4 import BeautifulSoup

import numpy as np
import pandas as pd
