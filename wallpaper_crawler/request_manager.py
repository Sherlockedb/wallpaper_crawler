import json
import os

from enum import Enum

class RequestStatus(Enum):
    DOING = 'doing'
    DONE = 'done'

class RequestPreiod(Enum):
    INIT = 'init'
    DETAILS = 'details'
    IMAGE = 'image'
    # COMPLETED = 'completed'

    def is_valid(name):
        return name in RequestPreiod.__members__.values()

def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance

@singleton
class RequestManager:
    
    def __init__(self, file_path, start_urls=None):
        """Initialize the request manager with start_urls."""
        self.file_path = file_path
        if not self._load_state() and start_urls:
            self.record_requests = {
                status.value: {
                    preiod.value: [] for preiod in RequestPreiod
                } for status in RequestStatus
            }
            self.record_requests[RequestStatus.DOING.value][RequestPreiod.INIT.value].extend(start_urls)
            self._save_state()

    def _load_state(self):
        """Load the state from file"""
        if not os.path.exists(self.file_path):
            return False
        with open(self.file_path, 'r') as f:
            self.record_requests = json.load(f)
        return True

    def _save_state(self):
        """Save the state to file"""
        with open(self.file_path, 'w') as f:
            json.dump(self.record_requests, f, indent=4)

    def add_urls(self, stage: RequestPreiod, urls):
        """Add URLs in a specific stage."""
        if not RequestPreiod.is_valid(stage):
            return False
        self.record_requests[RequestStatus.DOING.value][stage.value].extend(urls)
        self._save_state()
        return True

    def done_url(self, stage: RequestPreiod, url: str):
        """Add URLs in a specific stage."""
        if not RequestPreiod.is_valid(stage):
            return False
        if url in self.record_requests[RequestStatus.DOING.value][stage.value]:
            self.record_requests[RequestStatus.DOING.value][stage.value].remove(url)
        if url not in self.record_requests[RequestStatus.DONE.value][stage.value]:
            self.record_requests[RequestStatus.DONE.value][stage.value].append(url)
        self._save_state()
        return True

    def get_urls_by_stage(self, stage: RequestPreiod):
        """Get all URLs in a specific stage."""
        return self.record_requests[RequestStatus.DOING.value].get(stage.value, [])

    def move_url_to_stage(self, url, from_stage: RequestPreiod, to_stage: RequestPreiod):
        """Move a URL from one stage to another."""
        if url in self.record_requests[RequestStatus.DOING.value][from_stage.value]:
            self.record_requests[RequestStatus.DOING.value][from_stage.value].remove(url)
        if url not in self.record_requests[RequestStatus.DOING.value][to_stage.value]:
            self.record_requests[RequestStatus.DOING.value][to_stage.value].append(url)
        self._save_state()

    def is_processed(self, url, stage: RequestPreiod):
        """Check if the URL is already in a specific stage."""
        return url in self.record_requests[RequestStatus.DONE][stage.value]
