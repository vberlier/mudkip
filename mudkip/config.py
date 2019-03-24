import re
from pathlib import Path


AUTHOR_EXTRA = re.compile(r"<.*?>|\(.*?\)|\[.*?\]")
SPACES = re.compile(r"\s+")


def join_authors(authors):
    if not authors:
        return

    if isinstance(authors, str):
        string = authors
    elif len(authors) < 2:
        string = "".join(authors)
    else:
        string = ", ".join(authors[:-1]) + f" and {authors[-1]}"

    return SPACES.sub(" ", AUTHOR_EXTRA.sub("", string)).strip().replace(" ,", ",")


class Config:
    default_source_dir = "docs"
    default_output_dir = "docs/_build"

    def __init__(
        self,
        rtd=False,
        source_dir=None,
        output_dir=None,
        verbose=False,
        project_name=None,
        project_author=None,
        project_dir=None,
        dev_server=None,
        poetry=None,
    ):
        self.rtd = rtd
        self.dev_server = self.rtd if dev_server is None else dev_server
        self.poetry = {} if poetry is None else poetry

        self.mkdir = []

        self.source_dir = Path(source_dir or self.default_source_dir)
        self.output_dir = Path(output_dir or self.default_output_dir)
        self.verbose = verbose

        self.project_name = project_name or self.poetry.get("name")
        self.project_author = project_author or join_authors(self.poetry.get("authors"))

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

    def try_set_project_dir(self):
        self.project_dir = None

        if self.project_name:
            path = Path(self.project_name)

            if path.is_dir():
                self.project_dir = path
