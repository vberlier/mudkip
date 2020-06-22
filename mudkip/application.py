import sys
import time
import shutil
from os import path
from io import StringIO
from contextlib import contextmanager, nullcontext, ExitStack
import webbrowser

import tomlkit
from tomlkit.toml_file import TOMLFile as BaseTOMLFile
from sphinx.application import Sphinx
from sphinx.errors import SphinxError
from sphinx.util import logging
from recommonmark.transform import AutoStructify

from .config import Config
from .errors import MudkipError
from .jupyter import jupyter_notebook
from .npm import NpmDriver, locate_package_json
from .watch import DirectoryWatcher


class TOMLFile(BaseTOMLFile):
    def exists(self):
        return path.isfile(self._path)


class Mudkip:
    def __init__(
        self,
        *args,
        config=None,
        pyproject_file="pyproject.toml",
        mudkip_file="mudkip.toml",
        silence_pandoc_version_warning=True,
        **kwargs,
    ):
        pyproject = TOMLFile(pyproject_file)
        mudkip = TOMLFile(mudkip_file)

        if config is None:
            params = {}

            if pyproject.exists():
                tool = pyproject.read().get("tool", {})
                params.update(tool.get("mudkip", {}), poetry=tool.get("poetry"))

            if mudkip.exists():
                params.update(mudkip.read().get("mudkip", {}))

            params.update(kwargs)

            config = Config(*args, **params)

        self.config = config
        self.pyproject = pyproject
        self.mudkip = mudkip

        self.create_sphinx_application()
        self.configure_sphinx()

        package_json_dir = locate_package_json(config)
        self.npm_driver = (
            NpmDriver(package_json_dir, show_output=config.verbose)
            if package_json_dir
            else None
        )

        if silence_pandoc_version_warning:
            import nbconvert

            nbconvert.utils.pandoc._maximal_version = None

    def create_sphinx_application(self):
        extra_args = {}

        if not self.config.verbose:
            extra_args["status"] = None

        self.sphinx = Sphinx(
            self.config.sphinx_srcdir,
            self.config.sphinx_confdir,
            self.config.sphinx_outdir,
            self.config.sphinx_doctreedir,
            self.config.sphinx_buildername,
            self.config.sphinx_confoverrides,
            **extra_args,
        )

    def configure_sphinx(self):
        conf = self.sphinx.config

        if self.config.sphinx_project:
            conf.project = self.config.sphinx_project

        conf.copyright = time.strftime("%Y")

        if self.config.author:
            conf.author = self.config.author
            conf.copyright += ", " + conf.author

        if self.config.copyright:
            conf.copyright = self.config.copyright

        if self.config.version:
            conf.version = self.config.version

        if self.config.release:
            conf.release = self.config.release

        conf.master_doc = "index"
        conf.nitpicky = True

        conf.exclude_patterns = [
            ".*",
            "**/.*",
            "_*",
            "**/_*",
            "node_modules",
            "venv",
            str(self.config.output_dir),
        ]

        self.sphinx.setup_extension("recommonmark")

        recommonmark_config = {
            "enable_auto_toc_tree": True,
            "enable_math": True,
            "enable_inline_math": True,
            "enable_eval_rst": True,
        }

        self.sphinx.add_config_value("recommonmark_config", recommonmark_config, "env")
        self.sphinx.add_transform(AutoStructify)

        self.sphinx.setup_extension("nbsphinx")

        conf.nbsphinx_execute = "always"
        conf.nbsphinx_allow_errors = True

        self.sphinx.setup_extension("sphinx.ext.autodoc")
        self.sphinx.setup_extension("sphinx.ext.napoleon")
        self.sphinx.setup_extension("sphinx.ext.doctest")
        self.sphinx.setup_extension("sphinx.ext.autosectionlabel")
        self.sphinx.setup_extension("sphinx_autodoc_typehints")

        self.sphinx.setup_extension("mudkip.extension")

        self.sphinx._init_env(True)
        self.sphinx._init_builder()

    @contextmanager
    def sphinx_warning_is_error(self):
        try:
            original_value = self.sphinx.warningiserror
            self.sphinx.warningiserror = True
            yield
        finally:
            self.sphinx.warningiserror = original_value

    @contextmanager
    def sphinx_builder(self, buildername):
        try:
            original_builder = self.sphinx.builder
            self.sphinx.preload_builder(buildername)
            self.sphinx.builder = self.sphinx.create_builder(buildername)
            self.sphinx._init_env(False)
            self.sphinx._init_builder()
            yield
        finally:
            self.sphinx.builder = original_builder

    @contextmanager
    def sphinx_mute(self):
        try:
            original_status = self.sphinx._status
            original_warning = self.sphinx._warning
            self.sphinx._status = StringIO()
            self.sphinx._warning = StringIO()
            logging.setup(self.sphinx, self.sphinx._status, self.sphinx._warning)
            yield
        finally:
            self.sphinx._status = original_status
            self.sphinx._warning = original_warning
            logging.setup(self.sphinx, self.sphinx._status, self.sphinx._warning)

    @contextmanager
    def sphinx_config(self, **kwargs):
        not_present = object()
        conf = self.sphinx.config

        try:
            original_values = {}
            for key, value in kwargs.items():
                original_values[key] = getattr(conf, key, not_present)
                setattr(conf, key, value)
            yield
        finally:
            for key, value in original_values.items():
                if value is not_present:
                    delattr(conf, key)
                else:
                    setattr(conf, key, value)

    def init(self, title=None):
        table = tomlkit.table()
        table["title"] = title = (
            title or self.config.title or path.basename(path.abspath("."))
        )
        table["preset"] = self.config.preset.name

        source_dir = str(self.config.source_dir)
        output_dir = str(self.config.output_dir)

        if source_dir != self.config.default_source_dir:
            table["source_dir"] = source_dir

        if output_dir != self.config.default_output_dir:
            table["output_dir"] = output_dir

        table.add(tomlkit.nl())

        if self.mudkip.exists():
            doc = self.mudkip.read()

            if "mudkip" not in doc:
                doc["mudkip"] = table
            else:
                doc["mudkip"].update(table)

            self.mudkip.write(doc)

        elif self.pyproject.exists():
            doc = self.pyproject.read()
            tool = None

            try:
                tool = doc["tool"]
                tool["mudkip"].update(table)
            except KeyError:
                if tool is None:
                    doc["tool"] = {"mudkip": table}
                else:
                    tool["mudkip"] = table

            self.pyproject.write(doc)

        else:
            self.mudkip.write(tomlkit.document().add("mudkip", table))

        index_rst = self.config.source_dir / "index.rst"
        index_md = self.config.source_dir / "index.md"

        if not index_rst.is_file() and not index_md.is_file():
            index_rst.write_text(f"{title}\n{'=' * len(title)}\n")

    def build(self, *, check=False, skip_broken_links=False):
        try:
            self.delete_autodoc_cache()

            if check:
                self.clean()

                with self.sphinx_warning_is_error():
                    with self.sphinx_config(nbsphinx_allow_errors=False):
                        self.sphinx.build()

                        if not skip_broken_links:
                            with self.sphinx_builder("linkcheck"):
                                self.sphinx.build()
            else:
                self.sphinx.build()
        except SphinxError as exc:
            raise MudkipError(exc.args[0]) from exc

        if self.npm_driver:
            self.npm_driver.build()

    def delete_autodoc_cache(self):
        if not self.config.project_name:
            return

        modules = [
            mod
            for mod in sys.modules
            if mod == self.config.project_name
            or mod.startswith(self.config.project_name + ".")
        ]

        for mod in modules:
            del sys.modules[mod]

    def develop(
        self,
        open_browser=False,
        host="localhost",
        port=5500,
        notebook=False,
        notebook_host="localhost",
        notebook_port=8888,
        build_manager=None,
    ):
        if not build_manager:
            build_manager = lambda *args: nullcontext()

        patterns = [f"*{suff}" for suff in self.sphinx.config.source_suffix]
        ignore_patterns = self.sphinx.config.exclude_patterns

        dirs = [self.config.source_dir]

        if self.config.project_dir:
            dirs.append(self.config.project_dir)
            patterns.append("*.py")

        with ExitStack() as stack:
            stack.enter_context(self.sphinx_config(nbsphinx_execute="never"))

            notebook_url = None
            if notebook:
                notebook_url = stack.enter_context(
                    jupyter_notebook(
                        str(self.config.source_dir),
                        self.config.verbose,
                        notebook_host,
                        notebook_port,
                    )
                )

            server_url = None
            if self.config.dev_server:
                server_url = stack.enter_context(
                    self.config.dev_server(self.sphinx.outdir, host, port)
                )

                if open_browser:
                    try:
                        webbrowser.open(server_url)
                    except webbrowser.Error:
                        pass

            if self.npm_driver:
                stack.enter_context(self.npm_driver.develop())

            with build_manager(server_url=server_url, notebook_url=notebook_url):
                self.build()

            for event_batch in DirectoryWatcher(dirs, patterns, ignore_patterns):
                with build_manager(event_batch):
                    self.build()

    def test(self):
        with self.sphinx_builder("doctest"):
            with nullcontext() if self.config.verbose else self.sphinx_mute():
                self.build()

        output = self.config.sphinx_outdir / "output.txt"
        content = output.read_text() if output.is_file() else ""
        _, _, result = content.partition("\n\n")

        return self.sphinx.statuscode == 0, result.strip()

    def clean(self):
        try:
            shutil.rmtree(self.config.output_dir)
        except FileNotFoundError:
            pass

        if self.npm_driver:
            self.npm_driver.clean()
