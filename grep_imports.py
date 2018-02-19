"""A utility to grep through .py files and find import statements."""

from collections import Counter
from io import BytesIO
from itertools import chain, zip_longest
from operator import itemgetter
import os
import pickle
import re
import tarfile

import matplotlib.pyplot as plt
import pandas as pd


IGNORE = ('__pycache__', '.egg-info', '.dist-info')
PYEXTS = ('.py', '.pyx')


import_syntax = re.compile(r'^ *import +(?P<package>[.\w]+)(?: +as +\w+)? *$',
                           flags=re.MULTILINE)

# (?(id/name)yes-pattern|no-pattern)
#     --> (?(2)(?P<obj1>[*, \n\w]+)\)|(?P<obj2>[*, \w]+))
#     If id=2 exists (m.group(2)), look for optional newlines with
#     closing parentheses.  Otherwise, don't allow newlines.
from_syntax = re.compile(r'^ *from +(?P<package>[.\w]+) +import +(\()?(?(2)(?P<obj1>[*, \n\w]+)\)|(?P<obj2>[*, \w]+))$',
                         re.MULTILINE)

singlequotes = r"'''[^(?!''')]+'''"
doublequotes = r'"""[^(?!""")]+"""'


def drop_docstrings(text: str) -> str:
    """Remove docstrings from a body of text.

    We don't want import examples included in docstring example sections
    to be counted as module imports.
    """

    return re.sub(doublequotes, '', re.sub(singlequotes, '', text))


def grep_imports(text: str) -> str:
    """Extract *all* import statements from `text`."""
    text = drop_docstrings(text)
    grp1 = m.group('obj1')
    from_matchtypes = [(m.group('package'), re.sub(r'\s+', ' ', grp1 if
                       grp1 else m.group('obj2')).strip().split(', '))
                       for m in from_syntax.finditer(text)]
    import_matchtypes = import_syntax.findall(text)
    if not import_matchtypes:
        return from_matchtypes
    else:
        return from_matchtypes + list(zip_longest(
            import_syntax.findall(text), [None]))


def fileyielder(direc):
    """Yield (directory, package, [files]) triplets starting in `direc`."""
    ignore = re.compile('|'.join(IGNORE))
    for dirpath, _, filenames in os.walk(direc):
        if ignore.search(os.path.basename(dirpath)):
            continue
        else:
            pckg = dirpath.partition('/python3.6/')[-1].split('/')[0]
            if not pckg:
                # We're at top level i.e. .../lib./python3.6/
                pckg = 'STLIB'  # Standard Library
            elif pckg == 'site-packages':
                # Go one level further down to get to actual package
                pckg = dirpath.partition('/site-packages/')[-1].split('/')[0]
        files = tuple(f for f in filenames if f.endswith(PYEXTS))
        if not files:
            continue
        yield dirpath, pckg, files


def filter_imports(packagename, path):
    """Grep for imports but ignore intra-package references."""
    try:
        with open(path) as f:
            imports = grep_imports(f.read())
    except UnicodeDecodeError:
        # TODO: can we generalize this?
        with open(path, encoding='iso-8859-1') as f:
            imports = grep_imports(f.read())
    for package, objs in imports:
        if package.split('.')[0] == packagename or package.startswith('.'):
            # Intra-package reference; skip this one import statement
            continue
        else:
            # os.path -> os
            yield package.split('.')[0], objs


def filter_from_cols(frame):
    return tuple(filter_imports(frame['pckg'], frame['fullpath']))


def create_frame(direc):
    df = pd.DataFrame(list(fileyielder(direc)),
                      columns=['dirpath', 'pckg', 'files'])
    df = pd.concat((df, df.files.apply(pd.Series).add_prefix('file_')), axis=1)

    # Stack a Series of strings (.py modules) wide to long
    keys = [col for col in df if col.startswith('file_')]
    df = df.melt(id_vars=['pckg', 'dirpath', 'files'], value_vars=keys,
                 value_name='file')\
        .drop('variable', axis=1)\
        .sort_values(['pckg', 'dirpath', 'file'])\
        .dropna(subset=['file'])\
        .reset_index(drop=True)

    # Some libraries are structured as singlular modules with
    #     a root in site-packages
    #     i.e. lib/python3.6/site-packages/bz2file.py, site-packages/six.py
    # These don't have __init__ files but are still "libraries"
    df['pckg'] = df.pckg.where(df.pckg.ne(''), df.file.str.split('.').str[0])
    df['fullpath'] = df.dirpath.str.rstrip('/') + '/' + df.file
    assert all((os.path.isfile(f) for f in df.fullpath))

    df['imports'] = df.apply(filter_from_cols, axis=1)
    df['unique_imports'] = df.imports.apply(lambda x: set(i for i, _ in x))

    # Replace pckg=='STLIB' with the appropriate module name
    df['pckg'] = df.pckg.where(df.pckg.ne('STLIB'),
                               df.file.str.split('.py').str[0])
    return df


def compress_and_archive(objs, paths, archivename):
    """Add a batch of data structures directly to compressed archive."""
    with tarfile.open(archivename, 'w:gz') as archive:
        for path, obj in zip(paths, objs):
            tarinfo = tarfile.TarInfo(path)
            tarinfo.size = len(obj)
            archive.addfile(tarinfo, BytesIO(obj.encode('utf-8')))


def plot_count_subplots(pckgs, counts, titles, figsize: tuple, rotation: int,
                        fname: str, ylabel: str, suptitle: str, **kwargs):
    """Generically plot package/module names and corresponding frequencies.

    pckgs, counts: nested sequences
    titles: sequence
    """

    fig, axs = plt.subplots(1, 3, figsize=figsize)
    for title, (i, _), pckg, count in zip(
        titles, enumerate(axs), pckgs, counts):
        lbls, _ = zip(*enumerate(count))
        axs[i].bar(x=lbls, height=count)
        axs[i].set_xticks(lbls)
        axs[i].set_xticklabels(pckg, rotation=rotation, ha='right')
        if i == 0:
            axs[i].set_ylabel(ylabel)
        axs[i].set_title(title, loc='left', fontsize=16)
    fig.suptitle(suptitle, fontsize=18)
    plt.savefig(fname, **kwargs)


def plot_counts(pckgs, counts, title: str, figsize: tuple, rotation: int,
                fname: str, ylabel: str, **kwargs):
    """Single-axis (Axes) version of the above."""

    fig, ax = plt.subplots(figsize=figsize)
    lbls, _ = zip(*enumerate(counts))
    ax.bar(x=lbls, height=counts)
    ax.set_xticks(lbls)
    ax.set_xticklabels(pckgs, rotation=rotation, ha='right')
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc='left', fontsize=18)
    plt.savefig(fname, **kwargs)


def most_frequent(frames, n: int,
                  titles: str, figsize: tuple,
                  rotation: int, fname: str, **kwargs):
    """Aggregate unique imports across all packages."""
    counters = (Counter(chain.from_iterable(
                frame['unique_imports'])).most_common(n) for frame in frames)
    pckgs, counts = zip(*((tuple(map(itemgetter(0), counts)),
                           tuple(map(itemgetter(1), counts)))
                          for counts in counters))
    plot_count_subplots(pckgs, counts, titles=titles, figsize=figsize,
                        rotation=rotation, fname=fname,
                        ylabel='Import frequency',
                        suptitle='Most-imported packages/modules', **kwargs)


def rankby_atleast_one(frames, n: int, titles: str, figsize: tuple,
                       rotation: int, fname: str, normalize=True, **kwargs):
    """Packages ranked by times they are used *at least once* within all
       modules of other packages.  Normalized as percentage.
    """

    pckgs = []
    counts = []
    for frame in frames:
        grouped = frame.groupby('pckg')['unique_imports'].apply(
            lambda ser: set(chain.from_iterable(ser)))
        # Another ugly hack here because we can't pass `set()`
        #     to Series constructor
        count = grouped.apply(
            lambda s: pd.Series(tuple(s))).stack().value_counts()
        vc = count / len(count) if normalize else count
        if n:
            vc = vc.nlargest(n)
        pckg, count = vc.index, vc.values
        pckgs.append(pckg)
        counts.append(count)
    plot_count_subplots(pckgs, counts, titles=titles, figsize=figsize,
                        rotation=rotation, fname=fname,
                        ylabel='Pct. used at least once',
                        suptitle=('Most-imported packages/modules\n'
                                  'Frequency of times used at least once'
                                  ' per package'), **kwargs)


# Package-specific inputs
# ---------------------------------------------------------------------


def top_users(package: str, frame: pd.DataFrame, n: int,
              title: str, figsize: tuple,
              rotation: int, fname: str, **kwargs):
    """Given a `package` name, what other `n` packages use it most?

    This will count "duplicate" imports from within one module only once,
    but will count imports across modules within the same package.

    frame: constrain the data to this subset
    """

    users = frame.loc[frame['unique_imports'].apply(
        lambda s: package in s), 'pckg'].value_counts().nlargest(n)
    pckgs, counts = users.index, users.values
    plot_counts(pckgs, counts, title=title, figsize=figsize,
                rotation=rotation, fname=fname,
                ylabel='Number of %s imports' % package, **kwargs)


def most_used_by_pckg(package: str, frame: pd.DataFrame, n: int,
                      title: str, figsize: tuple,
                      rotation: int, fname: str, **kwargs):
    """Given `package`, what other packages does *it* use most frequently?"""
    counter = Counter(chain.from_iterable(frame.loc[frame['pckg'] == package,
                                            'unique_imports'])).most_common(n)
    pckgs, counts = zip(*counter)
    plot_counts(pckgs, counts, title=title, figsize=figsize,
                rotation=rotation, fname=fname,
                ylabel='Most frequently used imports within %s' % package,
                **kwargs)


def main():

    # "All" packages (Python Standard Library/built-ins, conda site-packages)
    py_direc = '/Users/brad/anaconda3/lib/python3.6/'
    df = create_frame(py_direc)

    # conda site-pacakges only
    sitepckg_direc = os.path.join(py_direc, 'site-packages/')
    sdf = create_frame(sitepckg_direc)

    # Excluding conda site-packages
    pydf = df.loc[~df.fullpath.str.contains('/site-packages/')]

    frames = (df, sdf, pydf)
    filenames = ('df', 'sdf', 'pydf')

    # Write json & flat file form to compressed archive
    here = os.path.abspath(os.path.dirname(__file__))
    archivename = os.path.join(here, 'imports.tar.gz')

    files = chain.from_iterable((frame.to_csv(index=False),
                                frame.to_json(orient='records'))
                               for frame in frames)
    paths = chain.from_iterable(('%s.csv' % name, '%s.json' % name)
                                for name in filenames)
    compress_and_archive(files, paths, archivename)

    with open(os.path.join(here, 'data.pickle'), 'wb') as f:
        pickle.dump(frames, f, pickle.HIGHEST_PROTOCOL)

    out = os.path.join(here, 'shapes.txt')
    with open(out, 'w') as f:
        print(*(df.shape for df in frames), file=f)

    titles = (
        'Standard Library + Anaconda Distribution',  # df
        'Anaconda Distribution',                     # sdf
        'Standard Library'                           # pydf
        )

    imgpath = os.path.join(here, 'imgs/')
    kwargs = {'figsize': (20, 10), 'n': 10, 'rotation': 50}


    most_frequent(frames=frames, titles=titles,
                  fname=os.path.join(imgpath, 'most_frequent.png'), **kwargs)

    rankby_atleast_one(frames=frames, titles=titles,
                       fname=os.path.join(imgpath, 'rankby_atleast_one.png'),
                       **kwargs)

    top_users('numpy', frame=sdf, title='Top Users of NumPy',
              fname=os.path.join(imgpath, 'top_users_numpy.png'), **kwargs)

    top_users('itertools', frame=sdf, title='Top Users of Itertools',
              fname=os.path.join(imgpath, 'top_users_itertools.png'), **kwargs)

    most_used_by_pckg('pandas', frame=df, title='Most-Used Imports in Pandas',
                      fname=os.path.join(imgpath, 'most_usedby_pandas.png'),
                      **kwargs)

if __name__ == '__main__':
    main()
