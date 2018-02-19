# flake8: noqa

'''Example module with a bunch of different import syntaxes.

Designed for sanity-testing.'''

# A comment

from __future__ import absolute_import, division, print_function

import functools
import itertools
import ctypes
try:
    from defusedexpat import pyexpat as expat
except ImportError:
    from xml.parsers import expat
    import xml

# Another comment here

try:
    from distributed import *
except:
    pass

import _collections_abc
from operator import itemgetter as _itemgetter, eq as _eq
from keyword import iskeyword as _iskeyword
import sys as _sys
import heapq as _heapq
from _weakref import proxy as _proxy

from pandas.core.sparse.api import *
from pandas.util._depr_module import _DeprecatedModule
from ._version import get_versions
from pandas.core.dtypes.common import *  # noqa

from . import event, util
from . import event, exc
from .pool import Pool

from pandas._libs import (hashtable as _hashtable,
                         lib as _lib,
                         tslib as _tslib)

from .sql.base import (
    SchemaVisitor
    )

from pandas import Series as ser, DataFrame as df
from NumPy import array

import os

from _pytest.config import (
    main, UsageError, cmdline,
    hookspec, hookimpl
)

from .ode import checkodesol, classify_ode, dsolve, \
    homogeneous_order

from .solveset import solveset, linsolve, linear_eq_to_matrix, nonlinsolve

from .solvers import solve, solve_linear_system, solve_linear_system_LU, \
    solve_undetermined_coeffs, nsolve, solve_linear, checksol, \
    det_quick, inv_quick, check_assumptions

from _csv import Error, __version__, writer, reader, register_dialect, \
                 unregister_dialect, get_dialect, list_dialects, \
                 field_size_limit, \
                 QUOTE_MINIMAL, QUOTE_ALL, QUOTE_NONNUMERIC, QUOTE_NONE, \
                 __doc__
from _csv import Dialect as _Dialect

___all__ = ['obj', 'f']

y = 5
obj = dict(a=1, b=2)
x = 5

def f(cond=False):
    '''Nonsense func.

    Example
    -------
    >>> from pyfile import f
    >>> f()
    '''

    if cond:
        import re
    print('Yep!')

if __name__ == '__main__':

    import os
    import sys
    f()
