# Data description

The compressed archive `imports.tar.gz` includes 3 tabular data structures, each exported as a JSON and CSV file (for a total of 6 files).

- `df`: This counts imports within modules that are both (1) from the Python Standard Library and (2) included with the Anaconda Distribution (MacOS, 64-bit Python 3.6).  This DataFrame occupies about 0.8 MB when using all `object` dtypes.
- `pydf`: This counts imports only from modules within the [Python Standard Library](https://docs.python.org/3/library/index.html), e.g. excluding anything within [`site-packages/`](https://www.python.org/dev/peps/pep-0370/).
- `sdf`: This is the opposite of `pydf`; it looks only in `site-packages/`, focusing on libraries that are [central to](https://www.anaconda.com/what-is-anaconda/) scientific computing in Python.

The JSON files are in "records" format.  (A list of dictionaries/mappings.)

Archive contents:

```
imports.tar.gz
├── df.csv
├── df.json
├── pydf.csv
├── pydf.json
├── sdf.csv
└── sdf.json
```

## Fields

Each table is in "tidy" (long) format and contains the following fields/columns:

- `file`: The file (module) name, i.e. `parser.py` or `__init__.py`.  In essense, this includes any file ending with `.py` or `.pyx` resulting from a recursive walk through the entire directory.
- `fullpath`: The absolute path of `file` (on my machine).  For example, `/Applications/anaconda3/lib/python3.6/site-packages/scipy/sparse/sparsetools.py`.
- `pckg`: The name of the top-level package (i.e. `dateutil`) to which `file` belongs.  Note that in some cases this may actually be a standalone _module_ that is not distributed in package form.  (For example: `six`, `os`--these behave mostly like packages but don't have `__init__.py` files, so their `pckg` is just `six` or `os` and their `file` fields are `six.py` and `os.py`, respectively.)
- `dirpath`: Full absolute path (on my machine) of the _nearest enclosing directory_ to `file`.  For example, this would be `/Applications/anaconda3/lib/python3.6/site-packages/astropy/io/ascii` for `rst.py` within the `astropy` package.  If `pckg` was just `functools`, (from the Standard Library) its corresponding `dirpath` would be `/Applications/anaconda3/lib/python3.6/`, because `functools.py` is located at this root with no intermediate package structure.
- `files`: A tuple of all modules (`.py` and `.pyx` files) included in this package.
- `imports`: A nested tuple of `(package, object)` pairs.  Again, `package` could technically be a true package (`pandas`) or a module (`collections`).  `object` is could be:
    - `None`, in the case that an `import x [as y]` syntax is used.
    - A list of `[obj1 [as name1], obj2 [as name2]]` from imports like `from itertools import zip_longest as izip_longest`
    - A list of one asterisk: `from matplotlib import *`.
- `unique_imports`: A set of the unique `package`s imported in the tuples from `imports`.

# Use of "package" versus "module"

While technically a [_package is a packaging of modules_](https://docs.python.org/3/tutorial/modules.html#packages), this project largely uses the terms "package" and "module" interchangably, to deal with cases in which a module is a "standalone" utility.  This occurs mostly within the Python Standard Library, but also for some modules such as `six` within the Anaconda distribution.
The reason is that when we say that some other module is "utilizing NumPy", we aren't concerned about which _module_ within NumPy is being used, only with the package (library) itself.

# Intra-package references

Intra-package references (imports within a package that import objects from elsewhere in that package) are ignored (dropped).  These may be of both relative or absolute form--for instance:

- Relative form: `from .solveset import solveset, linsolve, linear_eq_to_matrix, nonlinsolve`
- Absolute form: `from pandas._libs import hashtable as _hashtable` (somewhere within the pandas package).  This second case requires that we know the package name associated with that import, which is accomplished within `os.path.walk()`.

All other modules are allowed.  This would include imports from built-in (usually compiled) modules like `_functools`, for which `functools` is the Python wrapper.

# Testing details

I walked through my Python directory on a fresh install of the Anaconda Distribution (Feb 2018), using only the packages that come by default with the distribution.  Those can be found here:

> https://docs.anaconda.com/anaconda/packages/py3.6_osx-64

# Author

Brad Solomon <[brad.solomon.1124@gmail.com](mailto:brad.solomon.1124@gmail.com)\>
