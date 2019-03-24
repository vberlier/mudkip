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
def default(config):
    pass


@preset
def rtd(config):
    config.dev_server = True
    config.sphinx_buildername = "dirhtml"
    config.sphinx_confoverrides.update(html_theme="sphinx_rtd_theme")
