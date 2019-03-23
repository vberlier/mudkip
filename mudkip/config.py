from pathlib import Path

import toml


class Config:
    default_source_dir = "docs"
    default_output_dir = "docs/_build"
    default_dev_server_host = "127.0.0.1"
    default_dev_server_port = 5500

    def __init__(
        self,
        rtd=False,
        source_dir=None,
        output_dir=None,
        verbose=False,
        project_name=None,
        project_dir=None,
        dev_server=None,
        dev_server_host=None,
        dev_server_port=None,
    ):
        self.rtd = rtd
        self.dev_server = self.rtd if dev_server is None else dev_server
        self.dev_server_host = dev_server_host or self.default_dev_server_host
        self.dev_server_port = dev_server_port or self.default_dev_server_port

        self.mkdir = []

        self.source_dir = Path(source_dir or self.default_source_dir)
        self.output_dir = Path(output_dir or self.default_output_dir)
        self.verbose = verbose

        if project_name:
            self.project_name = project_name
        else:
            self.try_set_project_name()

        if project_dir:
            self.project_dir = project_dir
        else:
            self.try_set_project_dir()

        self.mkdir += self.source_dir, self.output_dir

        self.set_sphinx_arguments()

        for directory in self.mkdir:
            directory.mkdir(parents=True, exist_ok=True)

    def set_sphinx_arguments(self):
        self.sphinx_srcdir = self.source_dir
        self.sphinx_outdir = self.output_dir / "sphinx"
        self.sphinx_doctreedir = self.sphinx_outdir / ".doctrees"

        self.sphinx_buildername = "dirhtml" if self.rtd else "xml"

        self.sphinx_confdir = None
        self.sphinx_confoverrides = (
            {"html_theme": "sphinx_rtd_theme"} if self.rtd else {}
        )

    def try_set_project_name(self):
        try:
            with open("pyproject.toml") as pyproject:
                package_info = toml.load(pyproject)["tool"]["poetry"]
        except FileNotFoundError:
            self.project_name = None
        else:
            self.project_name = package_info["name"]

    def try_set_project_dir(self):
        self.project_dir = None

        if self.project_name:
            path = Path(self.project_name)

            if path.is_dir():
                self.project_dir = path
