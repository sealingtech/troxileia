import paramiko
from time import sleep
#TODO Allow reconfiguration of tap! Uncomment in reconfigure_gigamon #TODO
#Makes a map with pass all rule
def make_passall_map(channel, map_name, from_group, to_group):
    """
    Function that creates a pass all rules map on the GIgavue
    :param channel: a Parmaiko channel object
    :param map_name: name to give the new map
    :param from_group: name of port group that will be from
    :param to_group: name of port group that will be true
    """
    channel.send("map-passall alias "+ map_name + "\n")
    sleep(.25)
    channel.send("from " + from_group + "\n")
    sleep(.25)
    channel.send("to " + to_group + "\n")
    sleep(.25)
    channel.send("exit\n")
    sleep(.25)

#Makes a port group
def make_port_group(channel, group_name, port_list):
    """
    Functioan that creates a port-group on the Gigavue
    :param channel: a Paramiko channel object
    :param group_name: name of port group
    :param port_list: Python list of port names to inlcude in group
    """
    channel.send("port-group alias " + group_name + "\n")
    sleep(.25)
    port_string = ",".join(port for port in port_list)
    channel.send("port-list " + port_string + "\n")
    sleep(.25)
    channel.send("exit\n")

def make_gigastream(channel, stream_name, port_list):
    """
    Function that creates a gigastream
    :param channel: a paramiko channel object
    :param stream_name: name of the new Gigastream
    :param port_list: Python list of ports to add to Gigastream

    """
    channel.send("gigastream alias " + stream_name + "\n")
    sleep(.25)
    port_string = ",".join(port for port in port_list)
    channel.send("port-list " + port_string + "\n")
    sleep(.25)
    channel.send("exit\n")

def delete_passall_map(channel, map_name):
    """
    deletes passall_map in Gigavue
    :param channel: Paramiko channel object
    :param map_name: name of map to delete
    """
    channel.send("no map-passall alias " + map_name + "\n")


def delete_gigastream(channel, stream_name):
    """
    deletes gigastreame in Gigavue
    :param channel: Paramiko channel object
    :param stream_name: name of Gigastream to delete

    """
    channel.send("no gigastream alias " + stream_name + "\n")

def get_SSH(host, username, password):
    """
    Set up ssh stuff
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host, username=username, password=password)
    return ssh_client, ssh_client.invoke_shell()

def reconfigure_gigamon(host, username, password, port_list, map_name, from_group, stream_name):
    """
    Reconfigure the gigamon
    """
    print("Reconfiguration Started")
    client, channel = get_SSH(host, username, password)
    sleep(10)
    channel.send("enable\n")
    sleep(.25)
    channel.send("configure terminal\n")
    sleep(.25)
    delete_passall_map(channel, map_name)
    sleep(.25)
    delete_gigastream(channel, stream_name)
    sleep(.25)
    make_gigastream(channel, stream_name, port_list)
    sleep(.25)
    make_passall_map(channel, map_name, from_group, stream_name)
    sleep(.25)
    channel.send("write memory")
    sleep(.25)
    print("Reconfiguration Completed")
    client.close()