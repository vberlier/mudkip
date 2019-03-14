import sys

from sphinx.application import Sphinx
from sphinx.errors import SphinxError

from .config import Config
from .errors import MudkipError


class Mudkip:
    def __init__(self, config=None):
        if config is None:
            config = Config()

        self.config = config
        self.sphinx = self.create_sphinx_application()

    def create_sphinx_application(self):
        extra_args = {}

        if not self.config.verbose:
            extra_args["status"] = None

        return Sphinx(
            self.config.sphinx_srcdir,
            self.config.sphinx_confdir,
            self.config.sphinx_outdir,
            self.config.sphinx_doctreedir,
            self.config.sphinx_buildername,
            self.config.sphinx_confoverrides,
            **extra_args,
        )

    @property
    def watch_patterns(self):
        patterns = [f"**/*{suff}" for suff in self.sphinx.config.source_suffix]
        ignore_patterns = self.sphinx.config.exclude_patterns
        return patterns, ignore_patterns

    def build(self):
        try:
            self.sphinx.build()
        except SphinxError as exc:
            raise MudkipError(exc.args[0]) from exc
