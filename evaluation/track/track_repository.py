from dataclasses import dataclass
import itertools
from pathlib import Path
from typing import List

import natsort
import pandas as pd

from evaluation.common import InputType, Metaphor, ResultParam
from evaluation.questionnaire.questionnaire_repository import QuestionnaireRepository
from evaluation.track.recorded_track import RecordedTrack
from evaluation.track.reference_track import ReferenceTrack


@dataclass
class TrackRepository:
    reference_tracks: dict
    recorded_tracks: List[RecordedTrack]

    def __init__(self, user_ids: List[int] = None):
        reference_track_list = [ReferenceTrack(track_file) for track_file in Path(
            "reference_tracks").iterdir() if track_file.is_file()]
        self.reference_tracks = {
            track.track_id: track for track in reference_track_list}
        self.recorded_track_pathes = [track_path for track_path in Path(
            "recorded_tracks").iterdir() if track_path.is_file()]
        self.recorded_track_pathes = natsort.natsorted(
            self.recorded_track_pathes)
        self.recorded_tracks = [RecordedTrack(
            track_file) for track_file in self.recorded_track_pathes]
        self._evaluate()
        self.question_repo = QuestionnaireRepository()
        tracks = list(itertools.chain(*[self.get_by_user(user_id)
                      for user_id in user_ids])) if user_ids else self.get_all()
        data = {
            'UserId': [track.user_id for track in tracks],
            'Track':  [track.track_id for track in tracks],
            'InputAll': [f"{track.input_type.name}_{track.metaphor.name}" for track in tracks],
            'InputCategorized': [track.input_type.name for track in tracks],
            ResultParam.Time.name: [track.result.time for track in tracks],
            ResultParam.MeanError.name: [track.result.error_mean for track in tracks],
            ResultParam.MedianError.name: [track.result.error_median for track in tracks],
            ResultParam.PercentileError.name: [track.result.error_percentile for track in tracks],
            ResultParam.Distance.name: [track.result.distance for track in tracks],
            ResultParam.DeltaDistance.name: [track.result.delta_distance for track in tracks],
            ResultParam.ZoomMin.name: [track.result.zoom_min for track in tracks],
            ResultParam.ZoomMax.name: [track.result.zoom_max for track in tracks],
            ResultParam.ZoomMean.name: [track.result.zoom_mean for track in tracks],
            ResultParam.ZoomChange.name: [track.result.zoom_change for track in tracks],
        }
        self.data_frame = pd.DataFrame(data)

    def _evaluate(self):
        for track in self.recorded_tracks:
            reference_track = self.reference_tracks[track.track_id]
            track.evaluate(reference_track)

    def get_recorded_pathes(self) -> List[Path]:
        return self.recorded_track_pathes

    # type: ignore
    def get_by_track(self, track_id: int) -> List[RecordedTrack]:
        return [track for track in self.recorded_tracks if track.track_id == track_id]

    def get_by_user(self, user_id: int) -> List[RecordedTrack]:
        return [track for track in self.recorded_tracks if track.user_id == user_id]

    def get_by_input_type(self, input_type: InputType) -> List[RecordedTrack]:
        return [track for track in self.recorded_tracks if track.input_type == input_type]

    def get_by_metaphor(self, metaphor: Metaphor) -> List[RecordedTrack]:
        return [track for track in self.recorded_tracks if track.metaphor == metaphor]

    def get_all(self) -> List[RecordedTrack]:  # type: ignore
        return self.recorded_tracks

    def get_min_by_input(self, param: ResultParam):
        min_time_indices = self.data_frame.groupby(["UserId", "Track"])[
            param.name].idxmin()
        df_min_time = self.data_frame.loc[min_time_indices]
        return df_min_time[["UserId", "Track", "InputAll"]]

    def get_max_by_input(self, param: ResultParam):
        min_time_indices = self.data_frame.groupby(
            "UserId")[param.name].idxmax()
        df_min_time = self.data_frame.loc[min_time_indices]
        return df_min_time[["UserId", "InputAll"]]
