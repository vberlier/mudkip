from . import __version__


def process_doctree(app, doctree, docname):
    relations = app.env.collect_relations()
    parent, prev, next = relations.get(docname, (None,) * 3)

    attributes = {"name": docname, "parent": parent, "prev": prev, "next": next}

    for name, value in attributes.items():
        if value is not None:
            doctree[name] = value


def setup(app):
    app.connect("doctree-resolved", process_doctree)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
