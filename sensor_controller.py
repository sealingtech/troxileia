from kubernetes import config, client, watch
import gigamon
from os import environ
import time
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
    return node_dict


def watch_nodes(tap, port_list):
    """
    Reconfigures tap based on changes to sensor label on nodes
    """
#Authenticate based on in cluster or not
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()

    api = client.CoreV1Api()
    #Dictionary that stores node name and sensor value
    node_dict = get_initial_condition(api)

    #Watch for events occuring with nodes
    #While loops recreates watch object to restart for loop
    while True:
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
                        print(name + " sensor changed to " +  labels["sensor"])
                        node_dict[name] = labels["sensor"]
                        change = True

                #Only needed if possible to remove sensor label completely
                #Checks if sensor label was removed completely. Will update value
                #in node_dict to false
                else:
                    if node_dict[name] == "true":
                        node_dict[name] = "false"
                        change = True
                        print(name + " sensor label removed")

            #If there was a change and that port hasn't already been removed from
            #port_list, reconfig tap and add or remove from  port list
            #TODO Cleanup access to port_list?
            if change:

                if labels["sensor"] == "true":

                    #Check if port is already in port_list
                    if port_list.get_list().count(labels["port"]) == 0:
                        port_list.add(labels["port"])
                        print("Adding port " + labels["port"])
                    else:
                        continue
                else:

                    #Remove port if in port_list
                    try:
                        port_list.remove(labels["port"])
                        print("Removing port " + labels["port"])

                    #If port not in list, no need to reconfigure
                    except ValueError:
                        print(labels["port"] + " not in port_list to remove...")
                        continue
                tap.reconfigure(port_list.get_list())