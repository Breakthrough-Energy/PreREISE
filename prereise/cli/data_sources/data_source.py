from abc import ABCMeta, abstractmethod


class DataSource(metaclass=ABCMeta):
    """Abstract class that defines a strict interface
    that future data sources need to follow in order
    to seamlessly integrate with the parser.

    :param abc.ABCMeta metaclass: defaults to ABCMeta
    """

    @property
    @abstractmethod
    def command_name(self):
        """String command name for argparse. See add_parser function
        at `this link <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers>`_.
        """
        pass

    @property
    @abstractmethod
    def command_help(self):
        """String with a help description for the command. See add_parser function
        at `this link <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers>`_
        for more details
        """
        pass

    @property
    @abstractmethod
    def extract_arguments(self):
        """List of dictionaries defining the various flags and parameters
        the user needs to pass into this command, which are
        subsequently passed to the below extract function.
        See `add_argument <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument>`_
        to understand what is acceptable/unacceptable in these
        dictionaries.
        """
        pass

    @abstractmethod
    def extract(self):
        """Function that takes in the arguments defined in
        the above property extract_arguments and downloads
        the appropriate data and saves it somewhere.
        """
        pass
