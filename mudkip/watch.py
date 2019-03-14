from queue import Queue
from threading import Timer

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class QueueHandler(PatternMatchingEventHandler):
    debounce = 0.001

    def __init__(self, queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue
        self.timer = None

    def on_any_event(self, event):
        if self.timer is not None:
            self.timer.cancel()
        self.timer = Timer(self.debounce, self.debounced_callback, args=[event])
        self.timer.start()

    def debounced_callback(self, event):
        self.queue.put(event)
        self.timer = None


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
