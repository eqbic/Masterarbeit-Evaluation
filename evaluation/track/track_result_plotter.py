from typing import List

from matplotlib import pyplot as plt
import pandas as pd
from pandas.core.interchange.dataframe_protocol import DataFrame

from evaluation.common import InputFilter, ResultParam
from evaluation.questionnaire.questionnaire_repository import QuestionnaireRepository
from evaluation.track.track_repository import TrackRepository
import re

plt.rcParams['figure.dpi'] = 300  # Set resolution to 300 DPI
plt.rcParams['font.family'] = "Tahoma"

class TrackResultPlotter:
    def __init__(self, user_ids: List[int] = None):
        self.track_repo = TrackRepository(user_ids)
        self.question_repo = QuestionnaireRepository()

    def summary(self):
        return self.track_repo.data_frame.style.format(precision=2, )

    def plot_result(self, input: DataFrame, result_param: ResultParam, input_filter: InputFilter):
        # Group the data and calculate mean and std
        input_types = ['Touch_Gesture', 'Touch_Joystick', 'TUI_Joystick', 'TUI_Car']

        grouped_stats = input.groupby(['Track', input_filter.name])[result_param.name].agg(['mean', 'std']).reset_index()
        cmap = plt.cm.RdYlGn_r

        # Create figure with three subplots
        category_name = " ".join(re.split('(?<=.)(?=[A-Z])', result_param.name))
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle(f'{category_name} by Track and Input Type')

        tracks = [1, 2, 3]
        axes = [ax1, ax2, ax3]

        # Plot each track
        for track, ax in zip(tracks, axes):
            data = grouped_stats[grouped_stats['Track'] == track]
            if input_filter == InputFilter.InputAll:
                data = data.set_index(input_filter.name).reindex(input_types).reset_index()
            else:
                data = data.set_index(input_filter.name).reindex(["Touch", "TUI"]).reset_index()
            # Create bar plot
            track_data = data['mean']
            bars = ax.bar(data[input_filter.name], track_data)

            # Add error bars
            ax.errorbar(data[input_filter.name], track_data, yerr=data['std'],
                        fmt='none', color='black', capsize=5)

            # Customize plot
            ax.set_title(f'Strecke {track}')

            ax.set_ylabel(f'{category_name} (in Meter)')

            # Rotate x-axis labels for better readability
            ax.tick_params(axis='x', rotation=45)
            norm = plt.Normalize(track_data.min(), track_data.max())
            # Add value labels on bars
            for i, bar in enumerate(bars):
                height = bar.get_height()
                bar.set_facecolor(cmap(norm(height)))
                ax.text(bar.get_x() + bar.get_width() / 2., 0,
                        f'{height:.2f}',
                        ha='center', va='bottom')
                std = data['std'][i]
                ax.text(bar.get_x() + bar.get_width() / 2., height + std,
                        f'σ = {std:.2f}',
                        ha='center', va='bottom')

        plt.tight_layout()
        plt.show()

    def print_result(self, result_param: ResultParam, input_filter: InputFilter, aggfunc: str, min: float = None, max: float = None, plot=False, color=False):
        fixed_order = ["Touch_Gesture", "Touch_Joystick", "TUI_Joystick", "TUI_Car"]
        table = self.track_repo.data_frame.pivot_table(
            index=input_filter.name, columns="Track", values=result_param.name, aggfunc=[aggfunc], sort=False)
        if input_filter == InputFilter.InputAll:
            table = table.reindex(fixed_order)
        if plot:
            self.plot_result(self.track_repo.data_frame, result_param, input_filter)
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
