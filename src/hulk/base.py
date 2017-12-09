class Transformation(object):
    """
    Describes a source code transformation as a corresponding pair of Rooibos
    match and rewrite templates.
    """
    def __init__(self, match: str, rewrite: str) -> None:
        self.__match = match
        self.__rewrite = rewrite

    @property
    def match(self) -> str:
        return self.__match

    @property
    def rewrite(self) -> str:
        return self.__rewrite
