#Not currently being used
#Watch events as a whole and filter by object type
#Works, but gets noise at beginning of all events that have
#Happened before startup
def watchEvents():
    api = client.CoreV1Api()
    w = watch.Watch()
    for item in w.stream(api.list_event_for_all_namespaces, timeout_seconds=0):

        event = item["object"]
        obj = event.involved_object
        print(obj. kind + " " + event.reason)
       #Try to grab info from pod if it still exists
        if obj.kind == "Pod":
           try:
                pod = api.read_namespaced_pod(obj.name, obj.namespace)
                print("Success")
           except Exception:
                print("Pod could not be found")
"""

if __name__ == "__main__":
    #Authenticate based on in cluster or not
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()
    watchNodes()

[root@k8s-master project]# cat gigamon.py
import paramiko
from time import sleep

#Makes a map with pass all rule
def make_passall_map(channel, map_name, from_group, to_group):
    """
    Function that creates a pass all rules map on the GIgavue
    channel: a Parmaiko channel object
    map_name: name to give the new map
    from_group: name of port group that will be from
    to_group: name of port group that will be true
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
    channel: a Paramiko channel object
    group_name: name of port group
    port_list: Python list of port names to inlcude in group
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
    channel: a paramiko channel object
    stream_name: name of the new Gigastream
    port_list: Python list of ports to add to Gigastream

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
    channel: Paramiko channel object
    map_name: name of map to delete
    """
    channel.send("no map-passall alias " + map_name + "\n")


def delete_gigastream(channel, stream_name):
    """
    deletes gigastreame in Gigavue
    channel: Paramiko channel object
    stream_name: name of Gigastream to delete

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
    print("Reconfiguration started")
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
    print(channel.recv(2048).decode("utf-8"))
    print("Reconfiguration Completed")
    client.close()