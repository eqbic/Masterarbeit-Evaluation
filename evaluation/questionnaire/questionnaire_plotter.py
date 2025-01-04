from collections import defaultdict

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from evaluation.common import InputCombination, RankCategory
from evaluation.questionnaire.questionnaire_repository import QuestionnaireRepository

plt.rcParams['figure.dpi'] = 300  # Set resolution to 300 DPI
plt.rcParams['font.family'] = "Tahoma"

class QuestionnairePlotter:
    def __init__(self):
        self.repo = QuestionnaireRepository()
        self.colors = {
            InputCombination.TouchGesture: "lightcoral",
            InputCombination.TouchJoystick: "indianred",
            InputCombination.TuiJoystick: "brown",
            InputCombination.TuiCar: "firebrick"
        }

    def summary(self):
        return self.repo.data_frame.style.format()

    def print_sequence(self):
        for result in self.results:
            print(f"UserId: {result.user_id} -> {result.sequence}")

    def plot_age(self):
        ages = self.repo.get_ages()
        counts = ages.value_counts()
        counts.sort_index().plot(
            kind='bar',
            color='skyblue',
            title='Altersverteilung',
        )
        print(f"Mean: {ages.mean()}")
        print(f"Standard Deviation: {ages.std()}")
        plt.yticks(range(0,5))
        plt.show()

    def plot_rankings(self, category: RankCategory):
        key_value_counts = defaultdict(lambda: defaultdict(int))
        for d in self.repo.data_frame[category.name]:
            for key, value in d.items():
                key_value_counts[key][value] += 1

        num_keys = len(key_value_counts)
        fig, axes = plt.subplots(nrows=num_keys, figsize=(8, 4 * num_keys))
        for ax, (key, value_counts) in zip(axes, key_value_counts.items()):
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            x_values = [e.name for e in value_counts.keys()]
            y_values = list(value_counts.values())
            ax.bar(x_values, y_values)
            ax.set_title(f"{key}")
            ax.set_ylabel("Frequency")

    def plot_ranking(self):
        ranking = self.repo.get_ranking()
        input_types = [input_type.name for input_type in ranking.keys()]
        points = list(ranking.values())
        ax = plt.bar(input_types, points)
        plt.ylabel("Punkte")
        plt.title(
            "Sortiere die Varianten danach welche dir \nfür die Aufgabenstellung insgesamt am besten gefallen hat")

        for i, point in enumerate(points):
            text = f"{point} Pkt"
            plt.text(i, 0.1, text,
                     horizontalalignment='center',
                     verticalalignment='bottom')
        plt.show()

        return self.repo.get_ranking_raw()

    def plot_first_impression(self, normalized: bool = False):
        first_impressions = self.repo.get_first_impression(normalized)
        total_numbers = list(self.repo.get_first_impression(False).values())
        input_types = [
            input_type.name for input_type in first_impressions.keys()]


        points = np.array(list(first_impressions.values()))
        points = points * 100
        plt.bar(input_types, points)

        for i, (point, total) in enumerate(zip(points, total_numbers)):
            points_text = f"{total} ({point:.2f}%)"
            plt.text(i, 0.1, points_text,
                    horizontalalignment='center',
                    verticalalignment='bottom')
        plt.ylabel(f"Anteil (von {len(self.repo.results)})")
        plt.title(
            "Was denkst du welche Variante am besten \nfür die Aufgabenstellung geeignet ist?")
        plt.show()

    def plot_sequence(self):
        turns = self.repo.get_sequences()
        fig, axs = plt.subplots(2, 2)
        fig.set_size_inches(15, 10)
        fig.suptitle("Verteilung der Interaktionsformen pro Runde")
        axs_flat = axs.flatten()
        for k, v in turns.items():
            input_types = [
                input_type.name for input_type in v.keys()]
            points = list(v.values())
            for i, point in enumerate(points):
                axs_flat[k].text(i, 0.1, f"{point}",
                        horizontalalignment='center',
                        verticalalignment='bottom')
            axs_flat[k].set_title(f"Runde {k + 1}")
            axs_flat[k].bar(input_types, points)

    def mean_for_same_category(self, cell: tuple):
        if len(cell) == 1:
            return cell[0][0]
        elif len(cell) == 2:
            return (cell[0][0] + cell[1][0]) / 2

    def plot_usability(self, input_type: InputCombination):
        answers = self.repo.get_usabilities(input_type)
        sums = answers.map(self.mean_for_same_category)
        mean_of_sum = sums.mean()
        std_dev = sums.std()
        cmap = plt.cm.RdYlGn
        norm = plt.Normalize(1, 5)
        print(f"Standard Deviation:\n{std_dev}")
        ax = mean_of_sum.plot(
            kind="bar",
            title=input_type.name,
            yerr=std_dev,
            capsize=5,
        )
        ax.tick_params(axis='x', rotation=45)
        for bar, value in zip(ax.patches, mean_of_sum.values):
            bar.set_facecolor(cmap(norm(value)))

        for i, (value, std) in enumerate(zip(mean_of_sum, std_dev)):
            # Format std dev to 2 decimal places
            std_text = f'σ = {std:.2f}'
            value_text = f"{value:.2f}"
            # cv_text = f"CV = {std / value:.2f}"
            # Position the text above each bar (including error bars)
            ax.text(i, value + std + 0.1, std_text,
                    horizontalalignment='center',
                    verticalalignment='bottom')
            ax.text(i, 0.1, value_text,
                    horizontalalignment='center',
                    verticalalignment='bottom')
            # ax.text(i, value + std + 0.35, cv_text,
            #         horizontalalignment='center',
            #         verticalalignment='bottom')

        # plt.axhline(y=5, linestyle='--', color='b')
        plt.yticks(range(0,6))
        plt.ylim(0, 6)
        plt.tight_layout()
        plt.show()
        return answers

    def plot_usage_frequency(self):
        usage_frequency = self.repo.get_usage_frequency()
        return usage_frequency

