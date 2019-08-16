from kubernetes import config, client, watch
import gigamon
import sensor_controller
import pod_controller
import threading
import base64

def get_sensored_ports():
    """
    Returns dictionary of nodes in cluster with corresponding value of sensor
    Runs before Kubernets watch loop
    :param api: Kubernetes api object
    :returns: list of ports where the nodes are labeled sensor=true
    """
    #Dictionary that stores node name and sensor value
    port_list = list()
    api = client.CoreV1Api()
    #Get initial condition
    nodes = api.list_node(label_selector="sensor=true").items
    for node in nodes:
        port_list.append(node.metadata.labels["port"])

    return port_list

def get_secret_vars():
    """
    Reads in secret  variables for tap
    returns: dictionary  consisting of username, password
    """
    return client.CoreV1Api().list_namespaced_secret(field_selector="metadata.name=trox-secret", namespace="kube-system").items[0].data

def get_configmap_vars():
    """
    Reads in configmap  variables
    returns: dictionary  consisting of ip, tap_type, timeout, app_label
    """
    return client.CoreV1Api().list_namespaced_config_map(field_selector="metadata.name=trox-map", namespace="kube-system").items[0].data

class tap:
    """
    Defines a network tap that is thread locked

    """
    def __init__(self):
        """
        Initializes a tap with provided tap_type, a thread lock, and configmap variables used
        to log into the tap
        :param tap_type: type of netowrk tap
        """
        self.lock = threading.Lock()
        self.var_dict = get_secret_vars()
        self.config_map = get_configmap_vars()

    def reconfigure(self, port_list):
        """
        Reconfigures the tap with a given port_list
        :param port_list: list of ports to distribute load across
        """
        #Check type of tap
        if self.config_map["tap_type"] == "gigamon":
            for port in port_list:
                port.replace("_", "/")
            print("Reconfiguring for: ", port_list)
            self.lock.acquire()
            gigamon.reconfigure_gigamon(self.config_map["ip"], base64.b64decode(self.var_dict["username"]).decode("utf-8"), base64.b64decode(self.var_dict["password"]).decode("utf-8"), port_list, "sensor_map", "net_group", "sensor_stream")
            self.lock.release()

class locked_list:
    """
    Creates a thread locked list with basic append, release, and copy functions

    """
    def __init__(self, lst):
        """
        :param lst: list to pass in as parameter
        """
        self.lst = lst
        self.lock = threading.Lock()

    def add(self,item):
        """
        Adds item into self.lst through a lock
        :param item: item to append to list
        """
        self.lock.acquire()
        self.lst.append(item)
        self.lock.release()


    def remove(self, item):
        """
        Removes item from list through a lock
        :param item: item to remove from lst
        """
        self.lock.acquire()
        #Try to remove from list, if not, release lock and reraise exception
        try:
            self.lst.remove(item)
            self.lock.release()
        except ValueError as e:
            self.lock.release()
            raise e


    def get_list(self):
        """
        :return: shallow copy of self.lst
        """
        self.lock.acquire()
        lst = self.lst.copy()
        self.lock.release()
        return lst

if __name__=="__main__":
    #print Banner
    #prints properly in terminal
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
    tap = tap()
    port_list = locked_list(get_sensored_ports())
    tap.reconfigure(port_list.get_list())

    #Start controller threads
    sensor_thread = threading.Thread(target=sensor_controller.watch_nodes, args=(tap, port_list))
    pod_thread = threading.Thread(target=pod_controller.watch_pods, args=(tap, port_list))
    sensor_thread.start()
    pod_thread.start()
