from contextlib import contextmanager
from multiprocessing import Process, Queue

from notebook.notebookapp import NotebookApp


@contextmanager
def jupyter_notebook(source_dir, verbose, ip, port):
    try:
        queue = Queue()
        process = Process(
            target=notebook_process, args=(queue, source_dir, verbose, ip, port)
        )
        process.start()
        yield queue.get()
    finally:
        process.terminate()
        process.join()


def notebook_process(queue, source_dir, verbose, ip, port):
    Notebook.launch_instance(
        argv=[source_dir, "--no-browser"],
        queue=queue,
        verbose=verbose,
        ip=ip,
        port=port,
    )


class Notebook(NotebookApp):
    def __init__(self, *args, queue, verbose=False, ip=None, port=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not verbose:
            self.log.setLevel(100)
        if ip:
            self.ip = ip
        if port:
            self.port = port
        queue.put(self.display_url.split()[0])
