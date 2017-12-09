from hulk.exceptions import BadConfigFile
import yaml

class Config(object):
    @classmethod
    def from_file(cls, filename: str) -> 'Config':
        """
        Loads a configuration file from a given file.
        """
        with open(filename, 'r') as f:
            yml = yaml.load(f)

        if 'version' not in yml:
            raise BadConfigFile("expected 'version' property")

        if yml['version'] != '1.0':
            raise BadConfigFile("unexpected 'version' property; only '1.0' is currently supported.")

        return Config()

    def __init__(self):
        pass
