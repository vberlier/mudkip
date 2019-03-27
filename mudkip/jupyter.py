from contextlib import contextmanager
from multiprocessing import Process

from notebook.notebookapp import NotebookApp


@contextmanager
def jupyter_notebook(source_dir):
    try:
        process = Process(target=notebook_process, args=(source_dir,))
        process.start()
        yield
    finally:
        process.terminate()


def notebook_process(source_dir):
    Notebook.launch_instance(argv=[source_dir])


class Notebook(NotebookApp):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log.setLevel(100)
