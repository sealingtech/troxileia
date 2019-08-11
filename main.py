from kubernetes import config, client, watch
import gigamon
import sys
import time
import sensor_controller
import pod_controller
from os import environ
import threading

def get_sensored_ports(api):
    """
    Returns dictionary of nodes in cluster with corresponding value of sensor
    Runs before Kubernets watch loop
    """
    #Dictionary that stores node name and sensor value
    port_list = list()

    #Get initial condition
    nodes = api.list_node(label_selector="sensor=true").items
    for node in nodes:
        port_list.append(node.metadata.labels["port"])

    return port_list

def get_env_vars():
    """
    Reads in environmental variables for tap
    returns: dictionary  consisting of ip, username, password
    """
    var_dict = dict()
    var_dict["ip"] = environ.get("ip")
    var_dict["username"] = environ.get("username")
    var_dict["password"] = environ.get("password")
    return var_dict

class tap:

    def __init__(self, tap_type):
        self.tap_type =tap_type
        self.lock = threading.Lock()
        self.var_dict = get_env_vars()
    def reconfigure(self, port_list):
        #Check type of tap
        if self.tap_type == "gigamon":
            for port in port_list:
                port.replace("_", "/")
            print("Reconfiguring for: ", port_list)
            self.lock.acquire()
            gigamon.reconfigure_gigamon(var_dict["ip"], var_dict["username"], var_dict["password"], port_list, "sensor_map",     "net_group", "sensor_stream")
            self.lock.release()


class locked_list:
    def __init__(self, lst):
        self.lst = lst
        self.lock = threading.Lock()

    def add(self,item):
        self.lock.acquire()
        self.lst.append(item)
        self.lock.release()


    def remove(self, item):
        self.lock.acquire()
        #Try to remove from list, if not, release lock and reraise exception
        try:
            self.lst.remove(item)
            self.lock.release()
        except ValueError as e:
            self.lock.release()
            raise e


    def get_list(self):
        self.lock.acquire()
        lst = self.lst.copy()
        self.lock.release()
        return lst

if __name__=="__main__":
    print("\033[95m################################################################################")
    print("\__    ___/\______   \\_       \#\   \/  /|  \_    |###\__  _____/|  |#/  _  \###")
    print("##|    |####|       _/#/   |   \#\     /#|  ||    |####|    __)##|  |/  /_\  \##")
    print("##|    |####|    |   \/    |    \/     \#|  ||    |####|        \|  /    |    \#")
    print("##|____|####|____|_  /\_______  /___/\  \|__||______  /\________/|__\____|__  /#")
    print("###################\/#########\/######\_/###########\/######################\/##\033[0m")


    #Authenticate based on if running in the cluster
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()

    tap = tap(environ.get("tap_type"))
    var_dict = get_env_vars()
    api = client.CoreV1Api()
    port_list = locked_list(get_sensored_ports(api))
    tap.reconfigure(port_list.get_list())

    #TODO pass in tap, starting ports, var_dict
    sensor_thread = threading.Thread(target=sensor_controller.watch_nodes, args=(tap, port_list))
    pod_thread = threading.Thread(target=pod_controller.watch_pods, args=(tap, port_list))
    sensor_thread.start()
    pod_thread.start()