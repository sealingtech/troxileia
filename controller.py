from kubernetes import config, client, watch
import os
import json
#TODO Check if imported libararies are needed at end of development

#Watches pods in cluster
def watchPods():
    api = client.CoreV1Api()
    w = watch.Watch()
    for pod in w.stream(api.list_namespaced_pod,namespace="default", timeout_seconds=0):
        obj = pod["object"]
        meta = obj.metadata
        status = obj.status
        name = meta.name

        print(name + " has been " + pod["type"])

#Watches Nodes in cluster, looking for change to sensor label
def watchNodes():
    api = client.CoreV1Api()
    w = watch.Watch()
    #Dictionary that stores node name and sensor value
    node_dict = dict()
    #Watch for anything happening related to nodes
    for event  in w.stream(api.list_node, timeout_seconds=0):
        node = event["object"]
        meta = node.metadata
        labels = meta.labels
        status = node.status
        name = meta.name

        #Runs when node is added, adds node name and sensor status to dict
        #TODO Somehow check if current Gigamon configuration on startup
        #TODO Corresponds to what we expect based on sensor values
        if event["type"] == "ADDED":
            #if sensor is set and equal to true, value in dict is true
            if "sensor" in labels and labels["sensor"]== "true":
                node_dict[name] = "true"
            #if sensor is not set or is set to false, value in dict is false
            else:
                node_dict[name] = "false"
            print(name + " added sensor = " + node_dict[name])
        #Runs when node is modified. Checks if sensor was modified from value in node_dict
        if event["type"] == "MODIFIED":
            #Check if sensor is set
            if "sensor" in labels:
                #Check if previous value stored in node_dict and current value
                #are the same
                if labels["sensor"] != node_dict[name]:
                    print(name + " modified sensor changed to " +  labels["sensor"])
                    node_dict[name] = labels["sensor"]

            #Only needed if possible to remove sensor label completely
            #Checks if sensor label was removed completely. Will update value
            #in node_dict to false
            else:
                if node_dict[name] == "true":
                    node_dict[name] = "false"
                    print(name + " modified sensor label removed")

"""
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