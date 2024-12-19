from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from evaluation.common import InputCombination

bad_extremes = ["unangenehm", "ineffizient", "kompliziert",
                "nicht einleuchtend", "langweilig", "herkömmlich", "unberechenbar", "nutzlos"]
good_extremes = ["angenehm", "effizient", "einfach", "einleuchtend",
                 "spannend", "neuartig", "vorhersagbar", "nützlich"]
neutral = "neutral"
towards = "eher"


class UsabilityCategory(Enum):
    Attraktivität = 1
    Effizienz = 2
    Durchschaubarkeit = 3
    Stimulation = 4
    Originalität = 5
    Nützlichkeit = 6
    Steuerbarkeit = 7


categories = {
    "Insgesamt empfinde ich die Interaktion als": UsabilityCategory.Attraktivität,
    "Für das Erreichen meiner Ziele empfinde ich die Interaktion als": UsabilityCategory.Effizienz,
    "Die Interaktion empfinde ich als": UsabilityCategory.Durchschaubarkeit,
    "Die Bedienung wirkt auf mich": UsabilityCategory.Durchschaubarkeit,
    "Die Beschäftigung bzw. das Arbeiten empfinde ich als": UsabilityCategory.Stimulation,
    "Die Idee der Interaktion für diesen Anwendungsfall  finde ich": UsabilityCategory.Originalität,
    "Die Reaktion der Anwendung auf meine Eingaben und Befehle empfinde ich als": UsabilityCategory.Steuerbarkeit,
    "Die Möglichkeit diese Art der Interaktion zu nutzen empfinde ich als": UsabilityCategory.Nützlichkeit
}


@dataclass
class UsabilityAnswer:
    category: UsabilityCategory
    answer: str = ""
    points: int = 0

    def __init__(self, question: str, answer: str):
        self.category = categories[question]
        self.answer = answer
        if answer == "neutral":
            self.points = 3
        elif towards in answer:
            answer = answer.replace(towards, "").strip()
            if answer in bad_extremes:
                self.points = 2
            elif answer in good_extremes:
                self.points = 4
        elif answer in bad_extremes:
            self.points = 1
        else:
            self.points = 5


@dataclass
class UsabilityPerType:
    input_combination: InputCombination
    answers: List[UsabilityAnswer]

    def __init__(self, input_combination: InputCombination, answers: Dict[str, str]):
        self.input_combination = input_combination
        self.answers = []
        for question, answer in answers.items():
            self.answers.append(UsabilityAnswer(question, answer))
