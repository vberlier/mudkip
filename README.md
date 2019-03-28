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
