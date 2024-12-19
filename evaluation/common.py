from enum import Enum


class InputType(Enum):
    Touch = 1
    TUI = 2


class Metaphor(Enum):
    Gesture = 1
    Joystick = 2
    Car = 3


class InputCombination(Enum):
    TouchGesture = 1
    TouchJoystick = 2
    TuiJoystick = 3
    TuiCar = 4

    def __repr__(self):
        return self.name

    @staticmethod
    def build(input_type: InputType, metaphor: Metaphor):
        if input_type == InputType.Touch:
            if metaphor == Metaphor.Gesture:
                return InputCombination.TouchGesture
            if metaphor == Metaphor.Joystick:
                return InputCombination.TouchJoystick
        if input_type == InputType.TUI:
            if metaphor == Metaphor.Joystick:
                return InputCombination.TuiJoystick
            if metaphor == Metaphor.Car:
                return InputCombination.TuiCar


class InputFilter(Enum):
    InputAll = 1
    InputCategorized = 2


class RankCategory(Enum):
    Fastest = 1
    MostAccurate = 2
    Ranking = 3
    RankingPoints = 4


class ResultParam(Enum):
    Time = 1
    MeanError = 2
    MedianError = 3
    PercentileError = 4
    Distance = 5
    DeltaDistance = 6
    ZoomMin = 7
    ZoomMax = 8
    ZoomMean = 9
    ZoomChange = 10
