from pathlib import Path


class Config:
    default_source_dir = "docs"
    default_output_dir = "docs/_build"

    def __init__(self, source_dir=None, output_dir=None, verbose=False):
        self.mkdir = []

        self.source_dir = Path(source_dir or self.default_source_dir)
        self.output_dir = Path(output_dir or self.default_output_dir)
        self.verbose = verbose

        self.mkdir += self.source_dir, self.output_dir

        self.configure_sphinx()

        for directory in self.mkdir:
            directory.mkdir(parents=True, exist_ok=True)

    def configure_sphinx(self):
        self.sphinx_srcdir = self.source_dir
        self.sphinx_outdir = self.output_dir / "sphinx"
        self.sphinx_doctreedir = self.sphinx_outdir / ".doctrees"

        self.sphinx_buildername = "xml"

        self.sphinx_confdir = None
        self.sphinx_confoverrides = {
            "extensions": ["recommonmark"],
            "master_doc": "index",
            "source_suffix": {".rst": "restructuredtext", ".md": "markdown"},
            "exclude_patterns": [".*", "**/.*", "_*", "**/_*"],
        }
