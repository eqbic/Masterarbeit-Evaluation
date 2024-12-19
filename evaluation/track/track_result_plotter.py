from typing import List

from matplotlib import pyplot as plt
import pandas as pd

from evaluation.common import InputFilter, ResultParam
from evaluation.questionnaire.questionnaire_repository import QuestionnaireRepository
from evaluation.track.track_repository import TrackRepository


class TrackResultPlotter:
    def __init__(self, user_ids: List[int] = None):
        self.track_repo = TrackRepository(user_ids)
        self.question_repo = QuestionnaireRepository()

    def summary(self):
        return self.track_repo.data_frame.style.format(precision=2, )

    def print_result(self, result_param: ResultParam, input_filter: InputFilter, aggfunc: str, min: float = None, max: float = None, plot=False, color=False):
        table = self.track_repo.data_frame.pivot_table(
            index=input_filter.name, columns="Track", values=result_param.name, aggfunc=[aggfunc], sort=False)
        if plot:
            plt.figure()
            table.plot.bar()
        style = table.style
        if color:
            style = style.background_gradient(
                axis=0, cmap='Reds', vmin=min, vmax=max)
        return style.format(precision=2)

    def compare_with_questionnaire(self):
        user_ids = self.track_repo.data_frame["UserId"].unique().tolist()
        best_time_data = self.track_repo.get_min_by_input(ResultParam.Time)
        best_accuracy_data = self.track_repo.get_min_by_input(
            ResultParam.MeanError)
        # return data.loc[data["Track"] == 1]["InputAll"].tolist()
        best_time_data = {
            "UserId": [result.user_id for result in self.question_repo.results if result.user_id in user_ids],
            "Ranking": [result.ranking.values() for result in self.question_repo.results if result.user_id in user_ids],
            "EstimatedFastestTrack1": [result.fastest["Track 1"].name for result in self.question_repo.results if result.user_id in user_ids],
            "ActualFastestTrack1": best_time_data.loc[best_time_data["Track"] == 1]["InputAll"].tolist(),
            "EstimatedMostAccurateTrack1": [result.most_accurate["Track 1"].name for result in self.question_repo.results if result.user_id in user_ids],
            "ActualMostAccurateTrack1": best_accuracy_data.loc[best_accuracy_data["Track"] == 1]["InputAll"].tolist(),
            "EstimatedFastestTrack2": [result.fastest["Track 2"].name for result in self.question_repo.results if result.user_id in user_ids],
            "ActualFastestTrack2": best_time_data.loc[best_time_data["Track"] == 2]["InputAll"].tolist(),
            "EstimatedMostAccurateTrack2": [result.most_accurate["Track 2"].name for result in self.question_repo.results if result.user_id in user_ids],
            "ActualMostAccurateTrack2": best_accuracy_data.loc[best_accuracy_data["Track"] == 2]["InputAll"].tolist(),
            "EstimatedFastestTrack3": [result.fastest["Track 3"].name for result in self.question_repo.results if result.user_id in user_ids],
            "ActualFastestTrack3": best_time_data.loc[best_time_data["Track"] == 3]["InputAll"].tolist(),
            "EstimatedMostAccurateTrack3": [result.most_accurate["Track 3"].name for result in self.question_repo.results if result.user_id in user_ids],
            "ActualMostAccurateTrack3": best_accuracy_data.loc[best_accuracy_data["Track"] == 3]["InputAll"].tolist(),
        }
        data_frame = pd.DataFrame(best_time_data)
        return data_frame.style.format()
