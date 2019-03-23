from os import path
import logging
from contextlib import contextmanager
from multiprocessing import Process

from livereload import Server


@contextmanager
def dev_server(directory, host, port):
    try:
        process = Process(target=serve_directory, args=(directory, host, port))
        process.start()
        yield
    finally:
        process.terminate()


def serve_directory(directory, host, port):
    server = DevServer()
    server.watch(path.join(directory, "**", "*.html"))
    server.serve(port=port, host=host, root=directory)


class DevServer(Server):
    def _setup_logging(self):
        super()._setup_logging()
        logger = logging.getLogger("livereload")
        logger.setLevel(100)
