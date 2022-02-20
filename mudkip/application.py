import os
import shutil
import sys
import time
import webbrowser
from contextlib import ExitStack, contextmanager, nullcontext
from io import StringIO

import tomlkit
from myst_nb.render_outputs import get_default_render_priority
from sphinx.application import Sphinx
from sphinx.errors import SphinxError
from sphinx.util import logging
from tomlkit.toml_file import TOMLFile as BaseTOMLFile

from .config import Config
from .errors import MudkipError
from .github import GitHubPagesUpdater
from .jupyter import jupyter_notebook
from .npm import NpmDriver, locate_package_json
from .watch import DirectoryWatcher


class TOMLFile(BaseTOMLFile):
    def exists(self):
        return os.path.isfile(self._path)

    def extract(self, value=None):
        if value is None:
            return self.extract(self.read())

        value = getattr(value, "value", value)

        if isinstance(value, list):
            return [self.extract(x) for x in value]
        elif isinstance(value, dict):
            return {self.extract(key): self.extract(val) for key, val in value.items()}
        elif isinstance(value, tomlkit.items.Integer):
            return int(value)
        elif isinstance(value, tomlkit.items.Float):
            return float(value)
        elif isinstance(value, tomlkit.items.String):
            return str(value)
        elif isinstance(value, tomlkit.items.Bool):
            return bool(value)

        return value


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
                tool = pyproject.extract().get("tool", {})
                params.update(tool.get("mudkip", {}), poetry=tool.get("poetry"))

            if mudkip.exists():
                params.update(mudkip.extract().get("mudkip", {}))

            params.update(kwargs)

            config = Config(*args, **params)

        self.config = config
        self.pyproject = pyproject
        self.mudkip = mudkip

        self.create_sphinx_application()

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

        conf = self.config.sphinx_confoverrides

        if self.config.sphinx_project:
            conf.setdefault("project", self.config.sphinx_project)

        copyright = conf.setdefault("copyright", time.strftime("%Y"))

        if self.config.author:
            author = conf.setdefault("author", self.config.author)
            conf.setdefault("copyright", copyright + ", " + author)

        if self.config.copyright:
            conf.setdefault("copyright", self.config.copyright)
        if self.config.version:
            conf.setdefault("version", self.config.version)
        if self.config.release:
            conf.setdefault("release", self.config.release)
        if self.config.base_url:
            conf.setdefault("html_baseurl", self.config.base_url)

        conf.setdefault("master_doc", "index")
        conf.setdefault("nitpicky", True)
        conf.setdefault("smartquotes", False)

        conf.setdefault(
            "exclude_patterns",
            [
                ".*",
                "**/.*",
                "_*",
                "**/_*",
                "node_modules",
                "env",
                "venv",
                self.config.output_dir.name,
            ],
        )

        extensions = conf.setdefault("extensions", [])

        extensions.append("myst_nb")
        conf.setdefault("jupyter_execute_notebooks", "force")
        conf.setdefault("execution_allow_errors", True)
        conf.setdefault(
            "nb_render_priority", {"xml": get_default_render_priority("dirhtml")}
        )

        extensions.append("sphinx.ext.autodoc")
        conf.setdefault("autodoc_member_order", "bysource")
        conf.setdefault("autodoc_typehints", "description")
        conf.setdefault("autodoc_typehints_description_target", "documented")

        extensions.append("sphinx.ext.napoleon")
        extensions.append("sphinx.ext.doctest")

        if self.config.section_label_depth:
            extensions.append("sphinx.ext.autosectionlabel")
            conf.setdefault(
                "autosectionlabel_maxdepth", self.config.section_label_depth
            )

        extensions.append("sphinx.ext.intersphinx")
        conf.setdefault(
            "intersphinx_mapping", {"python": ("https://docs.python.org/3", None)}
        )

        extensions.append("mudkip.extension")

        self.sphinx = Sphinx(
            self.config.sphinx_srcdir,
            self.config.sphinx_confdir,
            self.config.sphinx_outdir,
            self.config.sphinx_doctreedir,
            self.config.sphinx_buildername,
            conf,
            **extra_args,
        )

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
            self.sphinx.builder.set_environment(self.sphinx.env)
            self.sphinx.builder.init()
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
            title or self.config.title or os.path.basename(os.path.abspath("."))
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

    def build(self, *, check=False, skip_broken_links=False, update_gh_pages=False):
        self.delete_autodoc_cache()

        if update_gh_pages:
            self.sphinx.setup_extension("sphinx.ext.githubpages")

        try:
            if check:
                self.clean()
                os.makedirs(self.sphinx.outdir, exist_ok=True)

                with self.sphinx_warning_is_error():
                    with self.sphinx_config(execution_allow_errors=False):
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

        if update_gh_pages:
            GitHubPagesUpdater(self.sphinx.outdir, self.config.repository).update()

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

        patterns += ["*.py", "*.pyi", "*.pyx", "*.js", "*.html", "*.css", "*.png"]

        dirs = [self.config.source_dir]

        if self.config.project_dir:
            dirs.append(self.config.project_dir)

        with ExitStack() as stack:
            stack.enter_context(self.sphinx_config(jupyter_execute_notebooks="auto"))

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
                        if notebook_url:
                            webbrowser.open(notebook_url)
                    except webbrowser.Error:
                        pass

            if self.npm_driver:
                stack.enter_context(self.npm_driver.develop())

            with build_manager(server_url=server_url, notebook_url=notebook_url):
                self.build()

            for event_batch in DirectoryWatcher(
                directories=dirs,
                patterns=patterns,
                ignore_patterns=ignore_patterns,
                output_directory=self.config.output_dir,
            ):
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
