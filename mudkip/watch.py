from queue import Queue

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class QueueHandler(PatternMatchingEventHandler):
    def __init__(self, queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue

    def on_any_event(self, event):
        self.queue.put(event)


def watch_directory(
    path,
    patterns=None,
    ignore_patterns=None,
    ignore_directories=False,
    case_sensitive=False,
    recursive=True,
):
    queue = Queue()

    observer = Observer()
    observer.schedule(
        QueueHandler(
            queue, patterns, ignore_patterns, ignore_directories, case_sensitive
        ),
        path,
        recursive,
    )

    observer.start()

    try:
        while True:
            yield queue.get()
    finally:
        observer.stop()
        observer.join()
