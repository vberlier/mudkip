# 📘 mudkip

[![PyPI](https://img.shields.io/pypi/v/mudkip.svg)](https://pypi.org/project/mudkip/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mudkip.svg)](https://pypi.org/project/mudkip/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

> A friendly [Sphinx](sphinx-doc.org) wrapper.

**🚧 Work in progress 🚧**

Mudkip is a small wrapper around [Sphinx](sphinx-doc.org) that bundles essential tools and extensions, providing everything needed for most day-to-day documentation.

```bash
$ mudkip --help
Usage: mudkip [OPTIONS] COMMAND [ARGS]...

  A friendly Sphinx wrapper.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  build    Build documentation.
  clean    Remove output directory.
  develop  Start development server.
  init     Initialize documentation.
  test     Test documentation.
```

## Features

Mudkip intends to provide an out-of-the-box solution for small to medium projects. The command-line utility lets you build and check your documentation, launch a development server with live reloading, run doctests and more!

Mudkip enables the following Sphinx extensions:

- [`sphinx.ext.autodoc`](http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html) for generating documentation from docstrings
- [`sphinx.ext.napoleon`](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html) for Google-style and NumPy-style docstrings support
- [`sphinx_autodoc_typehints`](https://github.com/agronholm/sphinx-autodoc-typehints) for pulling type information from Python 3 annotations
- [`sphinx.ext.doctest`](https://www.sphinx-doc.org/en/master/usage/extensions/doctest.html) for doctest support
- [`recommonmark`](https://recommonmark.readthedocs.io/en/latest/) for markdown support
- [`nbsphinx`](https://nbsphinx.readthedocs.io) for Jupyter notebook support

## Installation

The package can be installed with `pip`.

```bash
$ pip install mudkip
```

## Getting started

After installing the package, no need to run `sphinx-quickstart` or to configure anything, you can immediatly run the `develop` command and start writing docs.

```bash
$ mudkip develop
Watching "docs"...
Server running on http://localhost:5500
```

The command will create the "docs" directory if it doesn't already exist and launch a development server with live reloading. If you create an `index.rst` file and open the link in your browser, you'll see that mudkip uses the [Read the Docs](https://github.com/rtfd/sphinx_rtd_theme) theme by default.

> Note that mudkip enables the [`recommonmark`](https://recommonmark.readthedocs.io/en/latest/) extension, allowing you to use both reStructuredText and markdown files. You can totally create an `index.md` file instead if you prefer markdown over reStructuredText.

Press `Ctrl+C` at any time to exit.

### Building and checking documentation

The `build` command invokes Sphinx and builds your documentation. By default, the generated files are in "docs/.mudkip/dist".

```bash
$ mudkip build
Building "docs"...

Done.
```

Running the command with the `--check` flag will exit with code 1 if Sphinx reports any error or warning.

```bash
$ mudkip build --check
Building and checking "docs"...

All good.
```

The `--check` flag also makes sure that there are no broken links by running the [`linkcheck`](https://www.sphinx-doc.org/en/master/usage/builders/index.html#sphinx.builders.linkcheck.CheckExternalLinksBuilder) builder on your documentation.

### Running doctests

Mudkip enables the [`sphinx.ext.doctest`](https://www.sphinx-doc.org/en/master/usage/extensions/doctest.html) extension, making it possible to test interactive code examples. Try to add the following snippet to your `index` document:

```py
>>> import this
The Zen of Python, by Tim Peters
<BLANKLINE>
Beautiful is better than ugly.
...
```

The `test` command will run the code example and make sure that the output matches the documentation.

```bash
$ mudkip test
Testing "docs"...

Document: index
---------------
1 items passed all tests:
   1 tests in default
1 tests in 1 items.
1 passed and 0 failed.
Test passed.

Doctest summary
===============
    1 test
    0 failures in tests
    0 failures in setup code
    0 failures in cleanup code

Passed.
```

## Usage

> **TODO**

## Contributing

Contributions are welcome. This project uses [poetry](https://poetry.eustace.io/).

```bash
$ poetry install
```

The code follows the [black](https://github.com/ambv/black) code style.

```bash
$ poetry run black mudkip
```

---

License - [MIT](https://github.com/vberlier/mudkip/blob/master/LICENSE)
