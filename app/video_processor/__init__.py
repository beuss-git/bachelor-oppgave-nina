""" Video processor module. """


# TODO: Move this somewhere else
class Detection:  # pylint: disable=too-few-public-methods
    """A detection."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        label: str,
        confidence: float,
        xmin: int,
        ymin: int,
        xmax: int,
        ymax: int,
    ):
        self.label = label
        self.confidence = confidence
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
