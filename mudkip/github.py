import shutil
import subprocess
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory


class GitHubPagesUpdater:
    def __init__(self, upload_dir, repository):
        self.upload_dir = Path(upload_dir).absolute()
        self.repository = repository

    def update(self):
        with TemporaryDirectory() as tmp:
            shutil.copytree(self.upload_dir, tmp, dirs_exist_ok=True)

            run = partial(subprocess.run, check=True, cwd=tmp)

            run(["git", "init"])
            run(["git", "checkout", "-b", "gh-pages"])
            run(["git", "add", "."])
            run(["git", "commit", "-m", "Update GitHub Pages"])
            run(["git", "remote", "add", "origin", self.repository])
            run(["git", "push", "-f", "origin", "gh-pages"])
