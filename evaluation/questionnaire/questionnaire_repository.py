from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from typing import Dict, List

from pandas import DataFrame, Series

from evaluation.common import InputCombination, RankCategory
from evaluation.questionnaire.questionnaire_result import QuestionnaireResult
from evaluation.questionnaire.usability_per_type import UsabilityCategory


def parse_csv(path_to_csv: Path) -> DataFrame:
    with open(path_to_csv) as csv_file:
        return pd.read_csv(csv_file)

usage_frequencies = {
    "noch nie" : 0,
    "schon einmal genutzt": 1,
    "hin und wieder": 2,
    "regelmäßig": 5,
    "täglich": 8
}


@dataclass
class QuestionnaireRepository:
    results: List[QuestionnaireResult]

    def __init__(self):
        path_to_csv = Path('questionnaire_results/Fragebogen Masterarbeit.csv')
        self.data_frame: DataFrame = parse_csv(path_to_csv)
        self.results = self.parse_data_frame(self.data_frame)
        data = {
            'UserId': [result.user_id for result in self.results],
            'Age': [result.age for result in self.results],
            'Sequence': [result.sequence for result in self.results],
            'FirstImpression': [result.first_impression for result in self.results],
            RankCategory.Fastest.name: [result.fastest for result in self.results],
            RankCategory.MostAccurate.name: [result.most_accurate for result in self.results],
            RankCategory.Ranking.name: [result.ranking for result in self.results],
            'UsageFrequency': [self.get_usage_frequency_score(result.usage_frequency) for result in self.results],
            'Usability': [result.usabilities for result in self.results],
        }
        self.data_frame = pd.DataFrame(data)

    def get_usage_frequency_score(self, frequency_dict: Dict[str, str]) -> Dict[str, int]:
        result = {}
        for k,v in frequency_dict.items():
            result[k] = usage_frequencies[v]
        return result

    def get_usage_frequency(self, users: List[int] = None, just_total: bool = False):
        usage_frequency = self.data_frame.set_index("UserId")[["UsageFrequency"]]
        all_devices = set().union(*usage_frequency["UsageFrequency"].values)
        dict_data = {device: [row.iloc[0].get(device, 0) for _, row in usage_frequency.iterrows()]
                     for device in all_devices}
        df_expanded = pd.DataFrame(dict_data, index=usage_frequency.index)
        df_expanded['Total'] = df_expanded.sum(axis=1)
        if just_total:
            df_expanded = df_expanded[['Total']]
        if users is None:
            return df_expanded
        return df_expanded.reindex(users)

    def parse_data_frame(self, data_frame: DataFrame) -> List[QuestionnaireResult]:
        return [QuestionnaireResult(data_frame.loc[index]) for index in data_frame.index]

    def get_by_user(self, user_id: int) -> QuestionnaireResult:
        return [result for result in self.results if result.user_id == user_id][0]

    def get_ages(self):
        return self.data_frame["Age"]

    def get_first_impression(self, normalized: bool = False):
        first_impression_count = {
            InputCombination.TouchGesture: 0,
            InputCombination.TouchJoystick: 0,
            InputCombination.TuiJoystick: 0,
            InputCombination.TuiCar: 0
        }

        for result in self.results:
            first_impression_count[result.first_impression] += 1
        if normalized:
            for k, v in first_impression_count.items():
                first_impression_count[k] = v / len(self.results)
        return first_impression_count

    def get_ranking_raw(self):
        rankings = [
            ranking for ranking in self.data_frame[RankCategory.Ranking.name]]
        # for ranking in self.data_frame[RankCategory.Ranking.name]:
        #     ranking_per_user = [r.name for r in ranking.values()]
        #     rankings.append(ranking_per_user)
        data = {
            "UserId": self.data_frame["UserId"],
            "Ranking": rankings
        }
        pd.set_option("display.max_colwidth", None)
        frame = pd.DataFrame(data)
        frame.set_index("UserId", inplace=True)
        return frame

    def get_ranking(self) -> Dict[InputCombination, int]:
        ranking = {
            InputCombination.TouchGesture: 0,
            InputCombination.TouchJoystick: 0,
            InputCombination.TuiJoystick: 0,
            InputCombination.TuiCar: 0
        }
        for result in self.results:
            for k, v in result.ranking_points.items():
                ranking[k] += v
        return ranking

    def get_sequences(self):
        sequences = self.data_frame["Sequence"]
        turns = {
            0: {
                InputCombination.TouchGesture: 0,
                InputCombination.TouchJoystick: 0,
                InputCombination.TuiJoystick: 0,
                InputCombination.TuiCar: 0
            },
            1: {
                InputCombination.TouchGesture: 0,
                InputCombination.TouchJoystick: 0,
                InputCombination.TuiJoystick: 0,
                InputCombination.TuiCar: 0
            },
            2: {
                InputCombination.TouchGesture: 0,
                InputCombination.TouchJoystick: 0,
                InputCombination.TuiJoystick: 0,
                InputCombination.TuiCar: 0
            },
            3: {
                InputCombination.TouchGesture: 0,
                InputCombination.TouchJoystick: 0,
                InputCombination.TuiJoystick: 0,
                InputCombination.TuiCar: 0},
        }
        for sequence in sequences:
            for turn, input_type in enumerate(sequence):
                turns[turn][input_type] += 1
        return turns

    def get_points_by_category(self, data: Series, category: UsabilityCategory):
        result = []
        for user_data in data:
            points = []
            answers = []
            for answer in user_data.answers:
                if answer.category is not category:
                    continue
                points.append(answer.points)
                answers.append(answer.answer)

            result.append(tuple(zip(points, answers)))
        return result

    def get_usabilities(self, input_type: InputCombination):
        usabilities = self.data_frame["Usability"]
        results = [
            obj for sublist in usabilities for obj in sublist if obj.input_combination == input_type]

        data = {
            "UserId": self.data_frame["UserId"],
            UsabilityCategory.Attraktivität.name: self.get_points_by_category(results, UsabilityCategory.Attraktivität),
            UsabilityCategory.Effizienz.name: self.get_points_by_category(results, UsabilityCategory.Effizienz),
            UsabilityCategory.Steuerbarkeit.name: self.get_points_by_category(results, UsabilityCategory.Steuerbarkeit),
            UsabilityCategory.Originalität.name: self.get_points_by_category(results, UsabilityCategory.Originalität),
            UsabilityCategory.Stimulation.name: self.get_points_by_category(results, UsabilityCategory.Stimulation),
            UsabilityCategory.Nützlichkeit.name: self.get_points_by_category(results, UsabilityCategory.Nützlichkeit),
            UsabilityCategory.Durchschaubarkeit.name: self.get_points_by_category(results, UsabilityCategory.Durchschaubarkeit),

        }
        frame = pd.DataFrame(data)
        frame.set_index("UserId", inplace=True)
        return frame
