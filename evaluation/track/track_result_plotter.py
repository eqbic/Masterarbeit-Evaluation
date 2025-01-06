from typing import List

import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
from matplotlib.colors import ListedColormap
from pandas.core.interchange.dataframe_protocol import DataFrame

from evaluation.common import InputFilter, ResultParam, RankCategory, InputType
from evaluation.questionnaire.questionnaire_repository import QuestionnaireRepository
from evaluation.track.track_repository import TrackRepository
import re

plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.family'] = "Tahoma"

class TrackResultPlotter:
    def __init__(self, user_ids: List[int] = None):
        self.track_repo = TrackRepository(user_ids)
        self.question_repo = QuestionnaireRepository()

    def summary(self):
        return self.track_repo.data_frame.style.format(precision=2, )

    def plot_result(self, input: DataFrame, result_param: ResultParam, input_filter: InputFilter):
        # Group the data and calculate mean and std
        input_types = ['TouchGesture', 'TouchJoystick', 'TuiJoystick', 'TuiCar']

        grouped_stats = input.groupby(['Track', input_filter.name])[result_param.name].agg(['mean', 'std']).reset_index()
        cmap = plt.cm.RdYlGn_r

        # Create figure with three subplots
        category_name = " ".join(re.split('(?<=.)(?=[A-Z])', result_param.name))

        category_unit = "Meter"
        if result_param == ResultParam.Time:
            category_unit = "Seconds"
        elif result_param == ResultParam.ZoomChange or result_param == ResultParam.CombinedScore:
            category_unit = ""
        category_unit = "" if category_unit == "" else f"(in {category_unit})"
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
            if result_param == ResultParam.MeanError or result_param == ResultParam.MedianError:
                ax.set_ylim(-0.5, 3.5)
            elif result_param == ResultParam.Time:
                ax.set_ylim(0.0, 270.0)
            elif result_param == ResultParam.DeltaDistance:
                ax.set_ylim(-50.0, 120.0)
            elif result_param == ResultParam.ZoomChange:
                ax.set_ylim(-2.5, 8.0)
            elif result_param == ResultParam.CombinedScore:
                ax.set_ylim(0.0, 0.04)
            ax.set_ylabel(f'{category_name} {category_unit}')

            # Rotate x-axis labels for better readability
            ax.tick_params(axis='x', rotation=45)
            norm = plt.Normalize(track_data.min(), track_data.max())
            # Add value labels on bars
            for i, bar in enumerate(bars):
                height = bar.get_height()
                if height == 0:
                    continue
                # bar.set_facecolor(cmap(norm(height)))
                ax.text(bar.get_x() + bar.get_width() / 2., 0,
                        f'{height:.2f}',
                        ha='center', va='bottom')
                std = data['std'][i]
                ax.text(bar.get_x() + bar.get_width() / 2., height + std +(0.01 * ax.get_ylim()[1]),
                        f'σ = {std:.2f}',
                        ha='center', va='bottom')
                ax.text(bar.get_x() + bar.get_width() / 2., height + std + (0.07 * ax.get_ylim()[1]),
                        f"CV = {std / height:.2f}",
                        ha='center', va='bottom')


        plt.tight_layout()
        plt.show()

    def print_result(self, result_param: ResultParam, input_filter: InputFilter, aggfunc: str, min: float = None, max: float = None, plot=False, color=False):
        fixed_order = ["TouchGesture", "TouchJoystick", "TuiJoystick", "TuiCar"]
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

    def print_questionnaire_comparison(self, category: RankCategory):
        custom_cmap = ListedColormap(['#fca697', '#97fca9'])
        result = self.track_repo.get_questionnaire_comparison(category)

        bool_columns = [col for col in result.columns if col.endswith('_Correct')]
        matrix_data = np.array([[cell[0] for cell in result[col]] for col in bool_columns])
        total_values = matrix_data.size
        true_values = np.sum(matrix_data)
        percentage = (true_values / total_values) * 100
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))

        # Create the heatmap
        cmap = plt.cm.RdYlGn  # Red-Yellow-Green colormap
        im = ax.matshow(matrix_data, cmap=custom_cmap)

        # Add colorbar
        # plt.colorbar(im)

        track_labels = [col.replace('_Correct', '') for col in bool_columns]

        plt.title(f"Does the expectation match the actual performance for {category.name}: {percentage:.2f}%")

        # Add labels
        ax.set_yticks(np.arange(len(track_labels)))
        ax.set_xticks(np.arange(len(result)))
        ax.set_yticklabels(track_labels)
        ax.set_xticklabels(result['UserId'], rotation=45, ha='left')

        # Add text annotations in each cell
        for i in range(len(track_labels)):
            for j in range(len(result)):
                # Get the tuple values
                is_correct, estimated, actual = result[bool_columns[i]].iloc[j]
                text = ""
                if is_correct:
                    text = f"{estimated}"
                else:
                    text = f"{estimated}\n\n{actual}"
                ax.text(j, i, text, ha='center', va='center', color='black', fontsize=6)

        # Adjust layout to prevent label cutoff
        plt.tight_layout()

        # Show the plot
        plt.show()

    def print_usage_frequency_relations(self, result_param: ResultParam, count: int, input_type: InputType = None, low_to_high: bool = True):
        best_track_users = self.track_repo.get_best(result_param, count, input_type, low_to_high)
        user_list = best_track_users.index.tolist()
        usage_frequencies_for_users = self.question_repo.get_usage_frequency(user_list, just_total=True)
        return pd.concat([best_track_users, usage_frequencies_for_users], axis=1).round(3)