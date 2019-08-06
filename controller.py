from kubernetes import config, client, watch
import gigamon
import sys
from os import environ
#TODO Check if imported libararies are needed at end of development

def get_initial_condition(api):
    """
    Returns dictionary of nodes in cluster with corresponding value of sensor
    Runs before Kubernets watch loop
    """
    #Dictionary that stores node name and sensor value
    node_dict = dict()

    #Get initial condition
    nodes = api.list_node().items
    for node in nodes:
        labels = node.metadata.labels
        name = node.metadata.name
        #if sensor is set and equal to true, value in dict is true
        if "sensor" in labels and labels["sensor"]== "true":
            node_dict[name] = "true"
        #if sensor is not set or is set to false, value in dict is false
        else:
            node_dict[name] = "false"
        print(name + " added sensor = " + node_dict[name])
    return node_dict

def get_environmental_variables():
    """
    Reads in environmental variables
    returns: dictionary  consisting of ip, username, password
    """
    var_dict = dict()
    var_dict["ip"] = environ.get("ip")
    var_dict["username"] = environ.get("username")
    var_dict["password"] = environ.get("password")
    return var_dict

def reconfigure_tap(api, var_dict):
    """
    Reconfigures the based on nodes that currently have label sensor=true
    """
    sensored_nodes = api.list_node(label_selector="sensor=true").items
    ports = list()
    for node in sensored_nodes:
        ports.append(node.metadata.labels["port"].replace("_", "/"))
    print(ports)
    gigamon.reconfigure_gigamon(var_dict["ip"], var_dict["username"], var_dict["password"], ports, "sensor_map", "net_group", "sensor_stream")

def watch_nodes():
    """
    Reconfigures tap based on changes to sensor label on nodes
    """
    #Read in environmental variables
    var_dict = get_environmental_variables()

    api = client.CoreV1Api()
    #Dictionary that stores node name and sensor value
    node_dict = get_initial_condition(api)

    #Configure gigamon to intial condition
    reconfigure_tap(api, var_dict)

    #Watch for events occuring with nodes
    w = watch.Watch()
    for event in w.stream(api.list_node, timeout_seconds=0):

        node = event["object"]
        labels = node.metadata.labels
        name = node.metadata.name
        change = False

        #Runs when node is modified. Checks if sensor was modified from value in node_dict
        if event["type"] == "MODIFIED":
            #Check if sensor is set
            if "sensor" in labels:
                #Check if previous value stored in node_dict and current value
                #are different
                if labels["sensor"] != node_dict[name]:
                    print(name + " modified sensor changed to " +  labels["sensor"])
                    node_dict[name] = labels["sensor"]
                    change = True

            #Only needed if possible to remove sensor label completely
            #Checks if sensor label was removed completely. Will update value
            #in node_dict to false
            else:
                if node_dict[name] == "true":
                    node_dict[name] = "false"
                    change = True
                    print(name + " modified sensor label removed")

        #If there was a change, reconfig tap
        if change:
            reconfigure_tap(api, var_dict)

if __name__ == "__main__":
    #Authenticate based on in cluster or not
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()
    watch_nodes()