import dbus

from cell import CellConnection


class Sierra250U(CellConnection):
    """
    Context manager to connect to the Sprint Network using a Sierra Wireless
    250U.

    scripts from https://sites.google.com/site/cellularbeaglebone/
    """

    uuid = '02d5e625-86a7-448e-8880-91e0977ad4e5'
    nm_id = 'ting-sierra-250u'

s_con = dbus.Dictionary({
    'type': 'cdma',
    'uuid': '02d5e625-86a7-448e-8880-91e0977ad4e5',
    'autoconnect': True,
    'id': 'ting-sierra-250u'})

s_ipv4 = dbus.Dictionary({
    'method': 'auto'})

s_serial = dbus.Dictionary({
    'baud': 921600})

s_cdma = dbus.Dictionary({
    'number': '#777'
})

s_ipv6 = dbus.Dictionary({
    'method': 'auto'})

con = dbus.Dictionary({
    'connection': s_con,
    'cdma': s_cdma,
    'ipv4': s_ipv4,
    #'ipv6': s_ipv6,
    'serial': s_serial})

bus = dbus.SystemBus()
proxy = bus.get_object("org.freedesktop.NetworkManager", 
    "/org/freedesktop/NetworkManager/Settings")
settings = dbus.Interface(proxy, "org.freedesktop.NetworkManager.Settings")
settings.AddConnection(con)