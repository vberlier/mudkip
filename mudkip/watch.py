from queue import Queue
from threading import Timer
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class DirectoryWatcher:
    def __init__(
        self,
        directories=(),
        patterns=None,
        ignore_patterns=None,
        ignore_directories=False,
        case_sensitive=False,
        recursive=True,
        debounce_time=0.001,
    ):
        self.directories = set()
        self.patterns = patterns
        self.ignore_patterns = ignore_patterns
        self.ignore_directories = ignore_directories
        self.case_sensitive = case_sensitive
        self.recursive = recursive
        self.debounce_time = debounce_time

        for directory in directories:
            self.watch(directory)

        self.queue = Queue()
        self.timer = None
        self.events = []

    def watch(self, directory):
        directory = Path(directory).absolute()
        subdirs = set()

        for watched in self.directories:
            if directory in watched.parents:
                subdirs.add(watched)
            elif watched in directory.parents:
                return

        self.directories.add(directory)
        self.directories -= subdirs

    def __iter__(self):
        observer = Observer()

        for directory in self.directories:
            handler = PatternMatchingEventHandler(
                self.patterns,
                self.ignore_patterns,
                self.ignore_directories,
                self.case_sensitive,
            )
            handler.on_any_event = self.callback

            observer.schedule(handler, str(directory), self.recursive)

        observer.start()

        try:
            while True:
                yield self.queue.get()
        finally:
            observer.stop()
            observer.join()

    def callback(self, event):
        self.events.append(event)

        if self.timer:
            self.timer.cancel()

        self.timer = Timer(self.debounce_time, self.debounced_callback)
        self.timer.start()

    def debounced_callback(self):
        self.timer = None

        event_batch = self.events
        self.events = []

        self.queue.put(event_batch)
