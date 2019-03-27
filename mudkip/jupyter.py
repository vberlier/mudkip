from contextlib import contextmanager
from multiprocessing import Process

from notebook.notebookapp import launch_new_instance


@contextmanager
def jupyter_notebook(source_dir):
    try:
        process = Process(target=notebook_process, args=(source_dir,))
        process.start()
        yield
    finally:
        process.terminate()


def notebook_process(source_dir):
    try:
        launch_new_instance(argv=[source_dir])
    except KeyboardInterrupt:
        pass
