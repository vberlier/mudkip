import json
import subprocess
from contextlib import contextmanager
from pathlib import Path


def locate_package_json(config):
    cwd = Path.cwd()
    visited = {cwd.parent}

    for directory in (config.output_dir, config.source_dir, cwd):
        while directory not in visited:
            if (directory / "package.json").is_file():
                return directory

            visited.add(directory)
            directory = directory.parent
    return None


class NpmDriver:
    def __init__(self, directory, show_output=False):
        self.directory = directory
        self.show_output = show_output

        with (self.directory / "package.json").open() as pkg:
            self.package = json.load(pkg)

        self.use_yarn = (self.directory / "yarn.lock").is_file()
        self.scripts = self.package.get("scripts", {})

        self.current_process = None

    def run_script(self, *names, wait=True):
        if self.current_process:
            return None

        for name in names:
            if name in self.scripts:
                break
        else:
            return None

        output = None if self.show_output else subprocess.DEVNULL

        process = subprocess.Popen(
            (["yarn"] if self.use_yarn else ["npm", "run"]) + [name],
            cwd=self.directory,
            stdout=output,
            stderr=output,
        )

        if wait:
            process.wait()
        else:
            self.current_process = process

    def build(self):
        self.run_script("build")

    @contextmanager
    def develop(self):
        self.run_script("develop", "dev", "start", "serve", wait=False)

        try:
            yield
        finally:
            if self.current_process:
                self.current_process.terminate()

    def clean(self):
        self.run_script("clean")
