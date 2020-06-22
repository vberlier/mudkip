# 📘 mudkip

[![PyPI](https://img.shields.io/pypi/v/mudkip.svg)](https://pypi.org/project/mudkip/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mudkip.svg)](https://pypi.org/project/mudkip/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

> A friendly [Sphinx](https://sphinx-doc.org) wrapper.

**🚧 Work in progress 🚧**

Mudkip is a small wrapper around [Sphinx](https://sphinx-doc.org) that bundles essential tools and extensions, providing everything needed for documenting your projects.

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
- [`sphinx.ext.autosectionlabel`](https://www.sphinx-doc.org/en/master/usage/extensions/autosectionlabel.html) for referencing sections with their title
- [`recommonmark`](https://recommonmark.readthedocs.io/en/latest/) for markdown support and [`AutoStructify`](https://recommonmark.readthedocs.io/en/latest/auto_structify.html)
- [`nbsphinx`](https://nbsphinx.readthedocs.io) for Jupyter notebook support

Additional features are provided through an internal extension.

- `mdinclude` directive

  The built-in `include` directive doesn't handle markdown so mudkip provides an `mdinclude` directive to include markdown files.

  ```reStructuredText
  .. mdinclude:: ../README.md
  ```

  It's also possible to only include a specific section of the file with the `start-line` and `end-line` options.

  ```reStructuredText
  .. mdinclude:: ../README.md
    :start-line: 7
    :end-line: -3
  ```

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

The `build` command invokes the [`dirhtml`](https://www.sphinx-doc.org/en/master/usage/builders/index.html#sphinx.builders.dirhtml.DirectoryHTMLBuilder) builder and builds your documentation. By default, the generated files are in "docs/dist".

```bash
$ mudkip build
```

Running the command with the `--check` or `-c` flag will exit with code `1` if Sphinx reports any error or warning.

```bash
$ mudkip build --check
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

### Using Jupyter notebooks

The [`nbsphinx`](https://nbsphinx.readthedocs.io) extension provides support for Jupyter notebooks. This means that in addition to `.rst` and `.md` files, Sphinx will also generate pages for `.ipynb` files.

The `develop` command can launch the jupyter notebook in the "docs" directory and open it in your browser with the `--notebook` or `-n` flag.

```bash
$ mudkip develop --notebook
Watching "docs"...
Server running on http://localhost:5500
Notebook running on http://localhost:8888/?token=5e64df6...
```

With the `build` command, Notebooks are executed as part of the build process. The `--check` flag will make sure that there are no uncaught exceptions in any cell.

### Integration with npm and yarn

Mudkip can help you go further than regular Sphinx themes by running npm scripts for you if you're building your own front-end. If your docs contain a `package.json` file, Mudkip will invoke the appropriate npm script after running Sphinx using your preferred npm client.

```bash
$ mudkip build
```

Here, Mudkip would try to run either `npm run build` or `yarn build` before exiting the command. Similarly, `mudkip clean` would try to run either `npm run clean` or `yarn clean`.

```bash
$ mudkip develop
```

The `develop` command will try to run one of the following scripts: `develop`, `dev`, `start` or `serve`. If you don't have a dedicated script to run your project in development mode, Mudkip will simply execute the `build` script after running Sphinx each time you make a modification.

### Configuration

Mudkip doesn't require any configuration. You can however overwrite some of the default settings with command-line options or a configuration file.

For instance, when running a command, you can use the `--preset` or `-p` option to overwrite the default preset with `alabaster` if you want to use the [Alabaster](https://alabaster.readthedocs.io/en/latest/) theme instead of the default [Read the Docs](https://github.com/rtfd/sphinx_rtd_theme) theme.

```
$ mudkip build --preset alabaster
```

It's also possible to change the default source and output directories with the `--source-dir` and `--output-dir` options respectively.

```
$ mudkip build --source-dir path/to/docs --output-dir path/to/output
```

Passing these options to every single command can become tedious so you can use a configuration file to save your custom settings.

Running the `init` command will either add a `[tool.mudkip]` section to your `pyproject.toml` or create a `mudkip.toml` file with some basic configuration.

```bash
$ mudkip init
```

Here is the list of all the options that can be overwritten in the config file:

- `preset`

  default: `"rtd"`

  Presets configure mudkip and Sphinx to enable specific features. The `rtd` and `alabaster` presets enable the development server and configure Sphinx to use the `dirhtml` builder. The `rtd` preset also changes the html theme to the Read the Docs theme.

- `source_dir`

  default: `"docs"`

  This is the directory containing the source files for your documentation. Sphinx is configured to use it as its source directory and when the development server is enabled, mudkip will watch the directory for changes to rebuild your documentation.

- `output_dir`

  default: `"docs/dist"`

  The output directory is where Sphinx will output the generated files. This is also the directory served by the development server.

- `verbose`

  default: `false`

  This option can also be enabled on the command-line with the `--verbose` flag. Setting it to `true` will tell mudkip to display the entire Sphinx output as well as the Jupyter output when running the `develop` command with the `--notebook` flag.

- `project_name`

  default: The name of the project you're documenting in `pyproject.toml`

  If you're not using [poetry](https://poetry.eustace.io/), you will need to set it manually.

- `project_dir`

  default: The value of the `project_name` option

  Mudkip will watch the python files in your project directory when using the development server. This enables live reloading even when you're editing docstrings.

- `title`

  default: The value of the `project_name` option

  The project title used by Sphinx when building the documentation.

- `copyright`

  default: The current year followed by the value of the `author` option

  The copyright notice used by Sphinx when building the documentation.

- `author`

  default: The concatenated list of authors in `pyproject.toml`

  If you're not using [poetry](https://poetry.eustace.io/), you will need to set it manually.

- `version`

  default: The first two numbers of the `release` option

  The version used by Sphinx when building the documentation.

- `release`

  default: The project version in `pyproject.toml`

  If you're not using [poetry](https://poetry.eustace.io/), you will need to set it manually.

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
