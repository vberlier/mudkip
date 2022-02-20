import re
from os import path

from docutils.frontend import OptionParser
from docutils.io import StringOutput
from docutils.nodes import SkipNode
from docutils.writers import Writer
from sphinx.builders import Builder
from sphinx.util.osutil import ensuredir, os_path
from sphinx.writers.html import HTMLWriter
from sphinx.writers.html5 import HTML5Translator

HEADING_REGEX = re.compile(r".*(</h[123456]>).*")


class VitePressTranslator(HTML5Translator):
    def depart_title(self, node):
        super().depart_title(node)

        if m := HEADING_REGEX.match(self.body[-1]):
            title = ""
            tag = m[1].replace("/", "")
            level = int(tag[2])

            while True:
                fragment = self.body.pop()
                title = fragment + title
                if tag in fragment:
                    break

            before, _, title = title.partition(tag)
            title, _, after = title.partition(m[1])
            self.body.append(f"{before}\n\n{'#' * level} {title}\n\n{after}")

    def visit_literal_block(self, node):
        lang = node.get("language", "")
        self.body.append(f"\n\n```{lang}\n{node.rawsource.strip()}\n```\n\n")
        raise SkipNode


class VitePressBuilder(Builder):
    name = "vitepress"
    epilog = "The vitepress source files are in %(outdir)s."

    out_suffix = ".md"
    link_suffix = ".html"
    allow_parallel = True

    default_translator_class = VitePressTranslator

    add_permalinks = False

    def init(self):
        self.highlighter = None

    def get_outdated_docs(self):
        for docname in self.env.found_docs:
            if docname not in self.env.all_docs:
                yield docname
                continue
            targetname = path.join(self.outdir, docname + self.out_suffix)
            try:
                targetmtime = path.getmtime(targetname)
            except Exception:
                targetmtime = 0
            try:
                srcmtime = path.getmtime(self.env.doc2path(docname))
                if srcmtime > targetmtime:
                    yield docname
            except OSError:
                # source doesn't exist anymore
                pass

    def get_target_uri(self, docname, typ=None) -> str:
        return ""

    def prepare_writing(self, docnames):
        self.docwriter = HTMLWriter(self)
        self.docsettings = OptionParser(
            defaults=self.env.settings,
            components=(self.docwriter,),
            read_config_files=True,
        ).get_default_values()
        self.docsettings.compact_lists = bool(self.config.html_compact_lists)

    def write_doc(self, docname, doctree):
        destination = StringOutput(encoding="utf-8")
        doctree.settings = self.docsettings

        self.current_docname = docname
        self.secnumbers = self.env.toc_secnumbers.get(docname, {})
        self.fignumbers = self.env.toc_fignumbers.get(docname, {})

        self.docwriter.write(doctree, destination)
        self.docwriter.assemble_parts()
        body = self.docwriter.parts["fragment"]

        outfilename = path.join(self.outdir, os_path(docname) + self.out_suffix)
        ensuredir(path.dirname(outfilename))
        try:
            with open(outfilename, "w", encoding="utf-8") as f:
                f.write(body)
        except OSError:
            pass

    def finish(self):
        pass
