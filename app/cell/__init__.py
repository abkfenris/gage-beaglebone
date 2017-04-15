import NetworkManager

"""
Classes for cellular connections
"""


class CellConnection(object):
    """
    Base of cellular classes
    """

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, exc_type, exc_value, traceback):
        raise NotImplementedError



def list_connection_ids():
    """Returns a list of the ids of current connections"""
    return [con.GetSettings()['connection']['id'] for con in NetworkManager.Settings.ListConnections()]