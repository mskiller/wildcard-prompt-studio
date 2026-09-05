import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.worker_tasks import sync_file_to_db

logger = logging.getLogger(__name__)

class WorkspaceEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            sync_file_to_db.delay(event.src_path, "created")

    def on_modified(self, event):
        if not event.is_directory:
            sync_file_to_db.delay(event.src_path, "modified")

    def on_deleted(self, event):
        if not event.is_directory:
            sync_file_to_db.delay(event.src_path, "deleted")

class WorkspaceWatchdog:
    def __init__(self):
        self.observer = Observer()
        self.workspace_dir = os.getenv("WORKSPACE_DIR", "/workspace")
        self.handler = WorkspaceEventHandler()

    def start(self):
        if not os.path.exists(self.workspace_dir):
            os.makedirs(self.workspace_dir, exist_ok=True)
            
        self.observer.schedule(self.handler, self.workspace_dir, recursive=True)
        self.observer.start()
        logger.info(f"Started monitoring workspace: {self.workspace_dir}")

    def stop(self):
        self.observer.stop()
        self.observer.join()
        logger.info("Stopped monitoring workspace")

watchdog_service = WorkspaceWatchdog()
