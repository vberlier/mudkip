from os import path
import logging
from contextlib import contextmanager
from multiprocessing import Process

from livereload import Server


@contextmanager
def livereload_dev_server(directory, host, port):
    try:
        process = Process(
            target=LivereloadServer.serve_directory, args=(directory, host, port)
        )
        process.start()
        yield f"http://{host}:{port}"
    finally:
        process.terminate()
        process.join()


class LivereloadServer(Server):
    def _setup_logging(self):
        super()._setup_logging()
        logger = logging.getLogger("livereload")
        logger.setLevel(100)

    @classmethod
    def serve_directory(cls, directory, host, port):
        server = cls()
        server.watch(path.join(directory, "**", "*.html"))
        server.serve(port=port, host=host, root=directory)
