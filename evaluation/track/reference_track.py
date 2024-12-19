from dataclasses import dataclass
from pathlib import Path


@dataclass
class ReferenceTrack:
    track_id: int
    file: Path

    def __init__(self, file_path: Path):
        self.track_id = int(file_path.stem)
        self.file = file_path
