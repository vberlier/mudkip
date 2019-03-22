import sys
from io import StringIO
from contextlib import contextmanager
import shutil

from sphinx.application import Sphinx
from sphinx.errors import SphinxError
from sphinx.util import logging
from recommonmark.transform import AutoStructify

from .config import Config
from .errors import MudkipError
from .watch import DirectoryWatcher


class Mudkip:
    def __init__(self, config=None):
        if config is None:
            config = Config()

        self.config = config

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

        if self.config.project_name:
            conf.project = self.config.project_name

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

    def develop(self, *, build_manager=None):
        patterns = [f"*{suff}" for suff in self.sphinx.config.source_suffix]
        ignore_patterns = self.sphinx.config.exclude_patterns

        dirs = [self.config.source_dir]

        if self.config.project_dir:
            dirs.append(self.config.project_dir)
            patterns.append("*.py")

        for event_batch in DirectoryWatcher(dirs, patterns, ignore_patterns):
            if build_manager:
                with build_manager(event_batch):
                    self.build()
            else:
                self.build()

    def test(self):
        with self.sphinx_builder("doctest"):
            if self.config.verbose:
                self.build()
            else:
                with self.sphinx_mute():
                    self.build()

        output = self.config.sphinx_outdir / "output.txt"
        content = output.read_text() if output.is_file() else ""
        _, _, result = content.partition("\n\n")

        return self.sphinx.statuscode == 0, result.strip()

    def clean(self):
        shutil.rmtree(self.config.output_dir)
