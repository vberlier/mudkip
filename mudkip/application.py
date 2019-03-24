import sys
import time
import shutil
from io import StringIO
from contextlib import contextmanager, nullcontext

import tomlkit
from tomlkit.toml_file import TOMLFile
from sphinx.application import Sphinx
from sphinx.errors import SphinxError
from sphinx.util import logging
from recommonmark.transform import AutoStructify

from .config import Config
from .errors import MudkipError
from .server import dev_server
from .watch import DirectoryWatcher


class Mudkip:
    def __init__(self, *args, config=None, pyproject="pyproject.toml", **kwargs):
        if pyproject and not isinstance(pyproject, TOMLFile):
            pyproject = TOMLFile(pyproject)

        if config is None:
            params = {}

            if pyproject:
                try:
                    tool = pyproject.read()["tool"]
                    params.update(tool.get("mudkip", {}), poetry=tool.get("poetry"))
                except FileNotFoundError:
                    pass

            params.update(kwargs)

            config = Config(*args, **params)

        self.config = config
        self.pyproject = pyproject

        self.create_sphinx_application()
        self.configure_sphinx()

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

        conf.project = self.config.sphinx_project
        conf.copyright = time.strftime("%Y")

        if self.config.author:
            conf.author = self.config.author
            conf.copyright += ", " + conf.author

        if self.config.copyright:
            conf.copyright = self.config.copyright

        conf.version = self.config.version
        conf.release = self.config.release

        conf.master_doc = "index"
        conf.exclude_patterns = [".*", "**/.*", "_*", "**/_*"]

        self.sphinx.setup_extension("mudkip.extension")

        self.sphinx.setup_extension("recommonmark")

        recommonmark_config = {
            "enable_auto_toc_tree": True,
            "enable_math": True,
            "enable_inline_math": True,
            "enable_eval_rst": True,
        }

        self.sphinx.add_config_value("recommonmark_config", recommonmark_config, "env")
        self.sphinx.add_transform(AutoStructify)

        self.sphinx.setup_extension("sphinx.ext.autodoc")
        self.sphinx.setup_extension("sphinx.ext.napoleon")
        self.sphinx.setup_extension("sphinx.ext.doctest")
        self.sphinx.setup_extension("sphinx_autodoc_typehints")

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

    def init(self, title=None):
        table = tomlkit.table()
        table["title"] = title or self.config.title
        table["preset"] = self.config.preset.name

        source_dir = str(self.config.source_dir)
        output_dir = str(self.config.output_dir)

        if source_dir != self.config.default_source_dir:
            table["source_dir"] = source_dir

        if output_dir != self.config.default_output_dir:
            table["output_dir"] = output_dir

        table.add(tomlkit.nl())

        try:
            doc = self.pyproject.read()
            tool = None

            try:
                tool = doc["tool"]
                if "mudkip" not in tool:
                    tool._insert_after("poetry", "mudkip", table)
                else:
                    tool["mudkip"].update(table)
            except KeyError:
                if tool is None:
                    doc["tool"] = {"mudkip": table}
                else:
                    tool["mudkip"] = table

            self.pyproject.write(doc)
        except FileNotFoundError:
            pass

    def build(self, *, check=False, skip_broken_links=False):
        try:
            self.delete_autodoc_cache()

            if check:
                self.clean()

                with self.sphinx_warning_is_error():
                    self.sphinx.build()

                    if not skip_broken_links:
                        with self.sphinx_builder("linkcheck"):
                            self.sphinx.build()
            else:
                self.sphinx.build()
        except SphinxError as exc:
            raise MudkipError(exc.args[0]) from exc

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

    def develop(self, host="127.0.0.1", port=5500, build_manager=None):
        patterns = [f"*{suff}" for suff in self.sphinx.config.source_suffix]
        ignore_patterns = self.sphinx.config.exclude_patterns

        dirs = [self.config.source_dir]

        if self.config.project_dir:
            dirs.append(self.config.project_dir)
            patterns.append("*.py")

        if self.config.dev_server:
            server = dev_server(self.sphinx.outdir, host, port)
        else:
            server = nullcontext()

        with server:
            for event_batch in DirectoryWatcher(dirs, patterns, ignore_patterns):
                with build_manager(event_batch) if build_manager else nullcontext():
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
        shutil.rmtree(self.config.output_dir)
