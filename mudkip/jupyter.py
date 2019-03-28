from contextlib import contextmanager
from multiprocessing import Process

from notebook.notebookapp import NotebookApp


@contextmanager
def jupyter_notebook(source_dir, verbose, ip, port):
    try:
        process = Process(target=notebook_process, args=(source_dir, verbose, ip, port))
        process.start()
        yield
    finally:
        process.terminate()


def notebook_process(source_dir, verbose, ip, port):
    Notebook.launch_instance(argv=[source_dir], verbose=verbose, ip=ip, port=port)


class Notebook(NotebookApp):
    def __init__(self, *args, verbose=False, ip=None, port=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not verbose:
            self.log.setLevel(100)
        if ip:
            self.ip = ip
        if port:
            self.port = port
