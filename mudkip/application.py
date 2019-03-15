import sys

from sphinx.application import Sphinx
from sphinx.errors import SphinxError
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

    def build(self):
        try:
            self.sphinx.build()
        except SphinxError as exc:
            raise MudkipError(exc.args[0]) from exc

    def develop(self, build_manager):
        patterns = [f"*{suff}" for suff in self.sphinx.config.source_suffix]
        ignore_patterns = self.sphinx.config.exclude_patterns

        dirs = [self.config.source_dir]

        if self.config.project_dir:
            dirs.append(self.config.project_dir)
            patterns.append("*.py")

        for event_batch in DirectoryWatcher(dirs, patterns, ignore_patterns):
            # TODO: Remove sys.modules entries added by autodoc before building

            with build_manager(event_batch):
                self.build()
