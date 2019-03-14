from pathlib import Path

import toml


class Config:
    default_source_dir = "docs"
    default_output_dir = "docs/_build"

    def __init__(
        self, source_dir=None, output_dir=None, verbose=False, project_name=None
    ):
        self.mkdir = []

        self.source_dir = Path(source_dir or self.default_source_dir)
        self.output_dir = Path(output_dir or self.default_output_dir)
        self.verbose = verbose

        if project_name:
            self.project_name = project_name
        else:
            self.try_set_project_name()

        self.mkdir += self.source_dir, self.output_dir

        self.set_sphinx_arguments()

        for directory in self.mkdir:
            directory.mkdir(parents=True, exist_ok=True)

    def set_sphinx_arguments(self):
        self.sphinx_srcdir = self.source_dir
        self.sphinx_outdir = self.output_dir / "sphinx"
        self.sphinx_doctreedir = self.sphinx_outdir / ".doctrees"

        self.sphinx_buildername = "xml"

        self.sphinx_confdir = None
        self.sphinx_confoverrides = {}

    def try_set_project_name(self):
        try:
            with open("pyproject.toml") as pyproject:
                package_info = toml.load(pyproject)["tool"]["poetry"]
        except FileNotFoundError:
            return
        else:
            self.project_name = package_info["name"]
