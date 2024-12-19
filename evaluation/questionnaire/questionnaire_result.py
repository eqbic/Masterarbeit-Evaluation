from dataclasses import dataclass
from typing import Dict, List, Tuple

from evaluation.common import InputCombination, InputType, Metaphor
from evaluation.questionnaire.usability_per_type import UsabilityPerType


def parse_input_answer(answer: str) -> Tuple[InputCombination]:
    if answer == "Touch - Geste" or answer == "Touch - Gesten":
        return InputCombination.build(InputType.Touch, Metaphor.Gesture)
    elif answer == "Touch - Joystick":
        return InputCombination.build(InputType.Touch, Metaphor.Joystick)
    elif answer == "Tangible - Joystick":
        return InputCombination.build(InputType.TUI, Metaphor.Joystick)
    elif answer == "Tangible - Auto":
        return InputCombination.build(InputType.TUI, Metaphor.Car)


@dataclass
class QuestionnaireResult:
    user_id: int
    age: int
    sequence: List[Tuple[InputCombination]]
    usage_frequency: Dict[str, str]
    usabilities: List[UsabilityPerType]
    fastest: Dict[str, Tuple[InputCombination]]
    most_accurate: Dict[str, Tuple[InputCombination]]
    ranking: List[InputCombination]

    def __init__(self, answers):
        self.questions_per_input = 8
        self.start_indices = {
            "TouchGesture": 10,
            "TouchJoystick": 19,
            "TuiCar": 28,
            "TuiJoystick": 37
        }
        self.user_id = answers.iloc[1]
        self.age = answers.iloc[2]
        self.first_impression = parse_input_answer(answers.iloc[8])
        self.sequence = self._get_sequence(answers)
        self.usage_frequency = self._get_usage_frequency(answers)
        self.usabilities = self._get_usabilities(answers)
        self.fastest = self._get_fastest(answers)
        self.most_accurate = self._get_most_accurate(answers)
        self.ranking = self._get_ranking(answers)
        self.ranking_points = self._get_ranking_points(answers)

    def _get_sequence(self, answers):
        sequence = []
        next_input = answers.iloc[9]
        while next_input != "Fertig":
            parsed_answer = parse_input_answer(next_input)
            sequence.append(parsed_answer)
            next_index = self.start_indices[f"{
                parsed_answer.name}"] + self.questions_per_input
            next_input = answers.iloc[next_index]
        return sequence

    def _get_usage_frequency(self, answers) -> Dict[str, str]:
        return {"Smartphone": answers.iloc[3], "Tablet": answers.iloc[4], "Multitouch-Tisch": answers.iloc[5],
                "Tangibles": answers.iloc[6], "Videospiele": answers.iloc[7]}

    def _get_usabilities(self, answers) -> List[UsabilityPerType]:
        usabilities = []
        for input_combination in InputCombination:
            key = f"{input_combination.name}"
            if key not in self.start_indices.keys():
                continue

            start_index = self.start_indices[key]
            _answers = {}
            for index in range(start_index, start_index + self.questions_per_input):
                question = answers.index[index]
                answer = answers[question]
                _answers[question.split("[")[0].strip()] = answer
            usabilities.append(UsabilityPerType(input_combination, _answers))
        return usabilities

    def _get_fastest(self, answers):
        result = {}
        for track, i in enumerate(range(46, 49)):
            result[f"Track {track+1}"] = parse_input_answer(answers.iloc[i])
        return result

    def _get_most_accurate(self, answers):
        result = {}
        for track, i in enumerate(range(49, 52)):
            result[f"Track {track + 1}"] = parse_input_answer(answers.iloc[i])
        return result

    def _get_ranking(self, answers):
        result = {}
        for rank, i in enumerate(range(52, 56)):
            result[rank + 1] = (parse_input_answer(answers.iloc[i]))
        return result

    def _get_ranking_points(self, answers):
        result = {
            InputCombination.TouchGesture: 0,
            InputCombination.TouchJoystick: 0,
            InputCombination.TuiJoystick: 0,
            InputCombination.TuiCar: 0
        }
        for rank, i in enumerate(range(52, 56)):
            result[parse_input_answer(answers.iloc[i])] = (3 - rank)
        return result
