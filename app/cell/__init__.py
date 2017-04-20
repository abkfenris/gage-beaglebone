import NetworkManager
import dbus

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


def list_active_connections():
    """Returns a list of active connection names and IP addresses"""
    connections = []
    for conn in NetworkManager.NetworkManager.ActiveConnections:
        try:
            connections.append(conn.Id + ' - ' + ','.join(address['address']
                                                          for address
                                                          in conn.Ip4Config.AddressData))
        except AttributeError:
            pass
        except dbus.exceptions.DBusException:
            pass
    return connections