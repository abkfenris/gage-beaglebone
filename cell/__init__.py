"""
Classes for cellular connections
"""

GAGE_DIR = '/gage'


class CellConnection(object):
    """
    Base of cellular classes
    """

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, exc_type, exc_value, traceback):
        raise NotImplementedError
