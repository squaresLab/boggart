class Client(object):
    """
    A client for communicating with a Hulk server.
    """
    def __init__(self,
                 base_url: str,
                 timeout: int = 30):
        """
        Constructs a new client for communicating with a given Hulk server.

        Parameters:
            base_url:   the URL of the Hulk server.
            timeout:    the default timeout for API calls (in seconds).
        """
        self.__base_url = base_url
        self.__timeout = timeout
