import os

from docutils.core import ErrorString
from docutils.io import FileInput
from docutils.parsers import rst
from docutils.utils import new_document, relative_path
from myst_parser.sphinx_parser import MystParser

from . import __version__
from .vitepress import VitePressBuilder


def process_doctree(app, doctree, docname):
    relations = app.env.collect_relations()
    parent, prev, next = relations.get(docname, (None,) * 3)

    attributes = {"name": docname, "parent": parent, "prev": prev, "next": next}

    for name, value in attributes.items():
        if value is not None:
            doctree[name] = value


class MdInclude(rst.Directive):
    """Directive to include a markdown file.

    Adapted from https://github.com/miyakogi/m2r/blob/dev/m2r.py
    """

    required_arguments = 1
    option_spec = {"start-line": int, "end-line": int}

    def run(self):
        if not self.state.document.settings.file_insertion_enabled:
            raise self.warning('"%s" directive disabled.' % self.name)

        source = self.state_machine.input_lines.source(
            self.lineno - self.state_machine.input_offset - 1
        )
        source_dir = os.path.dirname(os.path.abspath(source))
        file_path = rst.directives.path(self.arguments[0])
        absolute_path = os.path.normpath(os.path.join(source_dir, file_path))
        path = relative_path(None, absolute_path)

        settings = self.state.document.settings

        try:
            settings.record_dependencies.add(path)
            include_file = FileInput(
                source_path=path,
                encoding=self.options.get("encoding", settings.input_encoding),
                error_handler=settings.input_encoding_error_handler,
            )
        except UnicodeEncodeError as error:
            raise self.severe(
                f'Problems with "{self.name}" directive path:\n'
                f'Cannot encode input file path "{path}" '
                "(wrong locale?)."
            )
        except IOError as error:
            raise self.severe(
                f'Problems with "{self.name}" directive path:\n{ErrorString(error)}.'
            )

        startline = self.options.get("start-line", None)
        endline = self.options.get("end-line", None)

        try:
            if startline or endline is not None:
                lines = include_file.readlines()
                rawtext = "".join(lines[startline:endline])
            else:
                rawtext = include_file.read()
        except UnicodeError as error:
            raise self.severe(
                f'Problem with "{self.name}" directive:\n{ErrorString(error)}'
            )

        document = new_document(absolute_path, settings)
        MystParser().parse(rawtext, document)

        return document.children


def setup(app):
    app.connect("doctree-resolved", process_doctree)
    app.add_directive("mdinclude", MdInclude)

    app.add_builder(VitePressBuilder)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
