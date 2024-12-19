from dataclasses import dataclass
from pathlib import Path

from evaluation.common import InputType, Metaphor
from evaluation.track import reference_track
from gps_accuracy.gps_accuracy import GpxEvaluator, GpxResult


@dataclass
class RecordedTrack:
    track_id: int
    user_id: int
    input_type: InputType
    metaphor: Metaphor
    file: Path
    result: GpxResult

    def __init__(self, file_path: Path):
        file_name = file_path.stem
        parts = file_name.split("_")
        self.user_id: int = int(parts[0])
        self.track_id: int = int(parts[1])
        self.input_type: InputType = InputType[parts[2]]
        self.metaphor: Metaphor = Metaphor[parts[3]]
        self.file: Path = file_path

    def evaluate(self, reference_track: reference_track):
        evaluator = GpxEvaluator(reference_track.file, self.file)
        self.result = evaluator.evaluate()
