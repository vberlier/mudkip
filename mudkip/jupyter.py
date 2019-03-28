from contextlib import contextmanager
from multiprocessing import Process

from notebook.notebookapp import NotebookApp


@contextmanager
def jupyter_notebook(source_dir, verbose):
    try:
        process = Process(target=notebook_process, args=(source_dir, verbose))
        process.start()
        yield
    finally:
        process.terminate()


def notebook_process(source_dir, verbose):
    Notebook.launch_instance(argv=[source_dir], verbose=verbose)


class Notebook(NotebookApp):
    def __init__(self, *args, verbose=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not verbose:
            self.log.setLevel(100)
