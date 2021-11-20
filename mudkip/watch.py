from functools import partial
from itertools import chain
from pathlib import Path
from queue import Empty, Queue
from threading import Timer
from typing import NamedTuple

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer


class EventBatch(NamedTuple):
    moved: list
    created: list
    modified: list
    deleted: list

    @property
    def all_events(self):
        return list(chain(self.moved, self.created, self.modified, self.deleted))


class EventHandler(PatternMatchingEventHandler):
    def __init__(
        self,
        patterns=None,
        ignore_patterns=None,
        ignore_directories=False,
        case_sensitive=False,
        output_directory=None,
    ):
        super().__init__(
            patterns=patterns,
            ignore_patterns=ignore_patterns,
            ignore_directories=ignore_directories,
            case_sensitive=case_sensitive,
        )
        self.output_directory = output_directory

    def dispatch(self, event):
        if self.output_directory:
            if path := getattr(event, "dest_path", getattr(event, "src_path", None)):
                if path.startswith(self.output_directory):
                    return
        return super().dispatch(event)


class DirectoryWatcher:
    def __init__(
        self,
        directories=(),
        patterns=None,
        ignore_patterns=None,
        ignore_directories=False,
        case_sensitive=False,
        output_directory=None,
        recursive=True,
        debounce_time=0.25,
        queue_timeout=2,
    ):
        self.directories = set()
        self.patterns = patterns
        self.ignore_patterns = ignore_patterns
        self.ignore_directories = ignore_directories
        self.case_sensitive = case_sensitive
        self.output_directory = output_directory and str(
            Path(output_directory).resolve()
        )
        self.recursive = recursive
        self.debounce_time = debounce_time
        self.queue_timeout = queue_timeout

        for directory in directories:
            self.watch(directory)

        self.queue = Queue()
        self.timer = None
        self.moved, self.created, self.modified, self.deleted = [], [], [], []
        self.created_paths = set()

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
            handler = EventHandler(
                self.patterns,
                self.ignore_patterns,
                self.ignore_directories,
                self.case_sensitive,
                self.output_directory,
            )
            handler.on_moved = partial(self.callback, self.moved)
            handler.on_created = partial(self.callback, self.created)
            handler.on_modified = partial(self.callback, self.modified)
            handler.on_deleted = partial(self.callback, self.deleted)

            observer.schedule(handler, str(directory), self.recursive)

        observer.start()

        try:
            while True:
                try:
                    yield self.queue.get(timeout=self.queue_timeout)
                except Empty:
                    pass
        finally:
            observer.stop()
            observer.join()

    def callback(self, category, event):
        if self.timer:
            self.timer.cancel()

        if all(e.src_path != event.src_path for e in category):
            category.append(event)

            if category is self.created:
                self.created_paths.add(event.src_path)

            if category in (self.modified, self.deleted):
                self.created[:] = [
                    e for e in self.created if e.src_path != event.src_path
                ]
            if category is self.deleted:
                self.modified[:] = [
                    e for e in self.modified if e.src_path != event.src_path
                ]
                if event.src_path in self.created_paths:
                    category.remove(event)

        self.timer = Timer(self.debounce_time, self.debounced_callback)
        self.timer.start()

    def debounced_callback(self):
        self.timer = None

        event_batch = EventBatch(
            list(self.moved),
            list(self.created),
            list(self.modified),
            list(self.deleted),
        )

        self.moved.clear()
        self.created.clear()
        self.modified.clear()
        self.deleted.clear()

        self.created_paths.clear()

        self.queue.put(event_batch)
