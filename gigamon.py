import paramiko
def _wait_for_execution(channel, string_check):
    """
    Checks for provided characters in the output stream
    Used to find when a command has been executed, prompt will show up when ready
    Ex: in stanard mode : gigamon-12345c >[SPACE]
    Ex: in enable/config mode: gigamon-12345c #[SPACE]
    String_check in those examples would be "> " or "# "
    :param channel: Paramiko channel connected to Giamon
    :string_check: String to check the stream for to signal prompt
    """
    check = False
    while not check:
        output = channel.recv(1024).decode("utf-8")
        if output[0-len(string_check):] == string_check:
            check = True

def make_passall_map(channel, map_name, from_group, to_group):
    """
    Function that creates a pass all rules map on the GIgavue
    :param channel: a Parmaiko channel object
    :param map_name: name to give the new map
    :param from_group: name of port group that will be from
    :param to_group: name of port group that will be true
    """
    channel.send("map-passall alias "+ map_name + "\n")
    _wait_for_execution(channel, "# ")
    channel.send("from " + from_group + "\n")
    _wait_for_execution(channel, "# ")
    channel.send("to " + to_group + "\n")
    _wait_for_execution(channel, "# ")
    channel.send("exit\n")
    _wait_for_execution(channel, "# ")


#Makes a port group
def make_port_group(channel, group_name, port_list):
    """
    Functioan that creates a port-group on the Gigavue
    :param channel: a Paramiko channel object
    :param group_name: name of port group
    :param port_list: Python list of port names to inlcude in group
    """
    channel.send("port-group alias " + group_name + "\n")
    _wait_for_execution(channel, "# ")
    port_string = ",".join(port for port in port_list)
    channel.send("port-list " + port_string + "\n")
    _wait_for_execution(channel, "# ")
    channel.send("exit\n")
    _wait_for_execution(channel, "# ")

def make_gigastream(channel, stream_name, port_list):
    """
    Function that creates a gigastream
    :param channel: a paramiko channel object
    :param stream_name: name of the new Gigastream
    :param port_list: Python list of ports to add to Gigastream

    """
    channel.send("gigastream alias " + stream_name + "\n")
    _wait_for_execution(channel, "# ")
    port_string = ",".join(port.replace("_","/") for port in port_list)
    channel.send("port-list " + port_string + "\n")
    _wait_for_execution(channel, "# ")
    channel.send("exit\n")
    _wait_for_execution(channel, "# ")

def delete_passall_map(channel, map_name):
    """
    deletes passall_map in Gigavue
    :param channel: Paramiko channel object
    :param map_name: name of map to delete
    """
    channel.send("no map-passall alias " + map_name + "\n")
    _wait_for_execution(channel, "# ")

def delete_gigastream(channel, stream_name):
    """
    deletes gigastreame in Gigavue
    :param channel: Paramiko channel object
    :param stream_name: name of Gigastream to delete

    """
    channel.send("no gigastream alias " + stream_name + "\n")
    _wait_for_execution(channel, "# ")

def get_SSH(host, username, password):
    """
    Set up ssh
    :param host: host to connect to
    :param username: username to connect to
    :param password: password to connect to
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host, username=username, password=password)
    ssh_channel = ssh_client.invoke_shell()
    _wait_for_execution(ssh_channel,"> ")
    return ssh_client, ssh_channel

def reconfigure_gigamon(host, username, password, port_list, map_name, from_group, stream_name):
    """
    Reconfigure the gigamon's sensor map and gigastream
    :param host:
    :param username:
    :param password:
    :param port_list:
    :param map_name:
    :param from_group:
    :param stream_name:
    """
    print("Reconfiguration Started")
    client, channel = get_SSH(host, username, password)
    channel.send("enable\n")
    _wait_for_execution(channel, "# ")
    channel.send("configure terminal\n")
    _wait_for_execution(channel, "# ")
    delete_passall_map(channel, map_name)
    delete_gigastream(channel, stream_name)
    make_gigastream(channel, stream_name, port_list)
    make_passall_map(channel, map_name, from_group, stream_name)
    channel.send("write memory\n")
    _wait_for_execution(channel, "# ")
    print("Reconfiguration Completed")
    client.close()
