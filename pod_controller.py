from kubernetes import config, client, watch
import gigamon
import sensor_controller
import sys
import time
from os import environ
import threading
#TODO Check if imported libararies are needed at end of development

class locking_queue:
    """
    Creates a queue that is thread locked
    """
    def __init__(self):
        self.queue = list()
        self.lock = threading.Lock()

    def enqueue(self, item):
        """
        Enqueues a new item, aquiring and releasing a lock immediately before and after
        :param item: item to add to queue
        """
        self.lock.acquire()
        self.queue.append(item)
        self.lock.release()

    def dequeue(self):
        """
        Dequeues item at index 0, acquiring and releasing lock immediately before and after
        """
        self.lock.acquire()
        self.queue.pop(0)
        self.lock.release()

    def exists_in_queue(self, item):
        """
        Checks if an item exists in the queue, acquring and releasing a lock immediately
        before and after access
        :param item: item to check for in queue
        :return: true or false, if item exists in queue
        """
        self.lock.acquire()
        count = self.queue.count(item)
        self.lock.release()
        return count != 0

#Gets pod condition
#Returns None if conditions list is none (pod recently created)
#Rerturns None if desired condtion not found in conditions list
def get_condition(condition_list, desired):
    """
    Gets a specified kubernetes pod condition from a list of conditions
    :param condition_list: List of Kubernetes Pod Conditions
    :param desired: desired condition to find in list
    :return: Kubernetes pod condition if found, None if not found or
            condition_list is None

    """
    if condition_list is None:
        return None
    for condition in condition_list:
        if condition.type == desired:
            return condition
    #Condition not found
    return None

def watch_pods(tap, port_list):
    #Authenticate based on in cluster or not
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()
    api = client.CoreV1Api()

    queue = locking_queue()
    timeout = int(environ.get("timeout"))
    app_label = environ.get("app_label")
    app_selector = "app=" + app_label
    while True:

        w = watch.Watch()
        #Loops through events occuring to pods
        #TODO Change ns back to default when done testing
        for event in w.stream(api.list_namespaced_pod,namespace="default",label_selector=app_selector, timeout_seconds=0):

            #check if pod was modified
            if event["type"] == "MODIFIED":
                pod = event["object"]
                condition = get_condition(pod.status.conditions, "Ready")

                #See if get_condition returned None
                if condition is None:
                    continue

                name = pod.metadata.name
                #Check if Pod is not ready and it not already in queue
                if condition.status != "True" and not queue.exists_in_queue(name):
                    x = threading.Thread(target=thread_func, args=(name, queue, timeout, port_list, tap))
                    x.start()


def thread_func(pod_name, queue, timeout, port_list, tap):
    """
    Function that runs in seperate thread
    Enqueues and dequeues pods into locked_queue,
    Reconfigures network tap if pod still down after timeout

    :param pod_name: name of pod to check on after timeout
    :param queue: locked_queue to enqueue and dequeue pod_names from
    :param timeout: time between when thread starts and when it checks on
    if pod is ready again

    """
    #Authenticate based on in cluster or not
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()
    print(pod_name + " became not ready, starting to monitor...")

    api = client.CoreV1Api()

    queue.enqueue(pod_name)
    time.sleep(timeout)
    queue.dequeue()

    print("Waited " + str(timeout) + "  seconds")

    #Try except used to catch when pods are no longer in cluster
    #This is because they properly terminated
    try:
        #Check if pod is now Ready
        #TODO change back to default ns when done testing
        pod = api.read_namespaced_pod(pod_name, "default")
        condition = get_condition(pod.status.conditions, "Ready")
        if condition is None:
            print("Ready Condtion does not exist, assume "+  pod_name +" properly terminated")
        else:
            #Check if tap needs to be reconfigured
            if condition.status != "True":

                #Find the node pod is on
                host_name = pod.spec.node_name

                #Find port on node
                node = api.list_node(field_selector = ("metadata.name="+host_name)).items[0]

                port = node.metadata.labels["port"]
                #Grab port_list and tap, reconfigure
                try:
                    port_list.remove(port)
                    tap.reconfigure(port_list.get_list())
                    print(host_name + " removed from tap: " + pod_name + " would not stay up")
                except ValueError as e:
                    print("The port " + pod_name + " is on is already removed")
                    pass
            else:
                print(pod_name + " is now ready")


    except:
        print(pod_name + " was terminated, no action required")
    print("exiting thread...")