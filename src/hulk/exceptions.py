class OperatorNameAlreadyExists(Exception):
    """
    Used to indicate that a given operator name is already in use by another
    operator.
    """
    def __init__(self, name: str):
        self.__name = name
        msg = "operator name is already in use: {}".format(name)
        super().__init__(msg)

    @property
    def name(self) -> str:
        return self.__name
