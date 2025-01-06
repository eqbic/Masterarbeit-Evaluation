from dataclasses import dataclass
import itertools
from pathlib import Path
from typing import List

import natsort
import pandas as pd
from pandas.core.interchange.dataframe_protocol import DataFrame

from evaluation.common import InputType, Metaphor, ResultParam, RankCategory
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
            'InputAll': [f"{track.input_combination.name}" for track in tracks],
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
            # ResultParam.CombinedScore.name: [self._calculate_performance_score(track.result.time,track.result.error_mean) for track in tracks],
        }
        self.data_frame = pd.DataFrame(data)
        self.data_frame = self.normalize_per_user_track(self.data_frame, ResultParam.MeanError)
        self.data_frame = self.normalize_per_user_track(self.data_frame, ResultParam.Time)
        self.data_frame = self.normalize_global(self.data_frame, ResultParam.MeanError)
        self.data_frame = self.normalize_global(self.data_frame, ResultParam.Time)
        self._set_performance_score()


    # normalizes values per user and track
    def normalize_per_user_track(self, dataset: pd.DataFrame, param: ResultParam) -> pd.DataFrame:
        dataset[f"normalized_{param.name}"] = dataset.groupby(['UserId', 'Track'])[param.name].transform(lambda x: (x / x.max()))
        return dataset

    def normalize_global(self, dataset: pd.DataFrame, param: ResultParam) -> pd.DataFrame:
        dataset[f"normalized_global_{param.name}"] = dataset.groupby('Track')[param.name].transform(lambda x: (x / x.max()))
        return dataset

    def _set_performance_score(self):
        self.data_frame[ResultParam.CombinedScore.name] = self.data_frame.apply(lambda row: self._calculate_performance_score(row["normalized_Time"], row["normalized_MeanError"]), axis=1)
        self.data_frame[ResultParam.CombinedScoreGlobal.name] = self.data_frame.apply(lambda row: self._calculate_performance_score(row["normalized_global_Time"], row["normalized_global_MeanError"]), axis=1)

    def _calculate_performance_score(self, time: float, error: float) -> float:
        if time == 0 and error == 0:
            return 1
        return (2 * time * error) / (time + error)

    def _evaluate(self):
        for track in self.recorded_tracks:
            reference_track = self.reference_tracks[track.track_id]
            track.evaluate(reference_track)

    def get_recorded_pathes(self) -> List[Path]:
        return self.recorded_track_pathes

    def get_by_track(self, track_id: int) -> List[RecordedTrack]:
        return [track for track in self.recorded_tracks if track.track_id == track_id]

    def get_by_user(self, user_id: int) -> List[RecordedTrack]:
        return [track for track in self.recorded_tracks if track.user_id == user_id]

    def get_by_input_type(self, input_type: InputType) -> List[RecordedTrack]:
        return [track for track in self.recorded_tracks if track.input_type == input_type]

    def get_by_metaphor(self, metaphor: Metaphor) -> List[RecordedTrack]:
        return [track for track in self.recorded_tracks if track.metaphor == metaphor]

    def get_all(self) -> List[RecordedTrack]:
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

    def _get_estimated_fastest(self, user_ids, track_id):
        data =[result.fastest for result in self.question_repo.results if result.user_id in user_ids]
        return [result[f"Track {track_id}"].name for result in data]

    def _get_estimated_most_accurate(self, user_ids, track_id):
        data = [result.most_accurate for result in self.question_repo.results if result.user_id in user_ids]
        return [result[f"Track {track_id}"].name for result in data]

    def _get_actual_data(self, base_data, track_id):
        return base_data.loc[base_data["Track"] == track_id]["InputAll"].tolist()

    def _get_estimated_data(self,category, user_ids, track_id):
        if category == RankCategory.Fastest:
            return self._get_estimated_fastest(user_ids, track_id)
        elif category == RankCategory.MostAccurate:
            return self._get_estimated_most_accurate(user_ids, track_id)

    def get_questionnaire_comparison(self, category: RankCategory):
        user_ids = self.data_frame["UserId"].unique().tolist()
        best_time_data = self.get_min_by_input(ResultParam.Time)
        best_accuracy_data = self.get_min_by_input(ResultParam.MeanError)

        actual_data = best_time_data if category == RankCategory.Fastest else best_accuracy_data

        data = {
            "UserId": [result.user_id for result in self.question_repo.results if result.user_id in user_ids],
            "EstimatedTrack1": self._get_estimated_data(category, user_ids, 1),
            "ActualTrack1": self._get_actual_data(actual_data, 1),
            "EstimatedTrack2": self._get_estimated_data(category, user_ids, 2),
            "ActualTrack2": self._get_actual_data(actual_data, 2),
            "EstimatedTrack3": self._get_estimated_data(category, user_ids, 3),
            "ActualTrack3": self._get_actual_data(actual_data, 3),
        }
        data_frame = pd.DataFrame(data)

        comparison_data = {
            "UserId": data_frame["UserId"],
            "Track1_Correct": list(zip(
                data_frame["EstimatedTrack1"] == data_frame["ActualTrack1"],
                data_frame["EstimatedTrack1"],
                data_frame["ActualTrack1"]
            )),
            "Track2_Correct": list(zip(
                data_frame["EstimatedTrack2"] == data_frame["ActualTrack2"],
                data_frame["EstimatedTrack2"],
                data_frame["ActualTrack2"]
            )),
            "Track3_Correct": list(zip(
                data_frame["EstimatedTrack3"] == data_frame["ActualTrack3"],
                data_frame["EstimatedTrack3"],
                data_frame["ActualTrack3"]
            )),
        }

        comparison_df = pd.DataFrame(comparison_data)
        return comparison_df

    def get_best(self, param: ResultParam, count: int, input_type: InputType, low_to_high: bool = True):
        if input_type is None:
            user_mean_error = self.data_frame.groupby("UserId")[param.name].mean()
        else:
            user_mean_error = self.data_frame[self.data_frame['InputCategorized']==input_type.name].groupby("UserId")[param.name].mean()
        if low_to_high:
            return user_mean_error.nsmallest(count)
        return user_mean_error.nlargest(count)