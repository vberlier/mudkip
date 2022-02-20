from .server import livereload_dev_server


def preset(func):
    Preset.register(Preset(func.__name__, func))
    return func


class Preset:
    registry = {}

    def __init__(self, name, callback=None):
        self.name = name
        self.callback = callback

    def execute(self, config):
        if self.callback:
            self.callback(config)

    @classmethod
    def register(cls, preset):
        cls.registry[preset.name] = preset
        return preset

    @classmethod
    def get(cls, name):
        return cls.registry[name]


@preset
def xml(config):
    pass


@preset
def alabaster(config):
    config.dev_server = livereload_dev_server
    config.sphinx_buildername = "dirhtml"


@preset
def rtd(config):
    alabaster(config)
    config.override.setdefault("html_theme", "sphinx_rtd_theme")


@preset
def furo(config):
    alabaster(config)
    config.override.setdefault("html_theme", "furo")
    config.override.setdefault("html_css_files", []).append("mudkip_furo.css")


@preset
def vitepress(config):
    config.sphinx_buildername = "vitepress"
    config.override.setdefault("nb_render_priority", {}).setdefault(
        "vitepress",
        (
            "application/vnd.jupyter.widget-view+json",
            "application/javascript",
            "text/html",
            "image/svg+xml",
            "image/png",
            "image/jpeg",
            "text/markdown",
            "text/latex",
            "text/plain",
        ),
    )
