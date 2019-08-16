from kubernetes import config, client, watch
import time
import threading

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
    """
    Watch pods, and if one is consistently crashing, reconfigure the newtwork tap
    :param tap: thread locked network tap shared with sensor_controller
    :param port_list: locked_list shared with sensor_controller
    """
    #Authenticate based on in cluster or not
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()
    api = client.CoreV1Api()

    queue = locking_queue()
    var_dict = config_map = client.CoreV1Api().list_namespaced_config_map(field_selector="metadata.name=controller-config", namespace="kube-system").items[0].data
    timeout = var_dict["timeout"]
    app_label = var_dict["app_label"]
    app_selector = "app in(" + app_label + ")"
    #Start controller loop
    while True:

        w = watch.Watch()
        #Loops through events occuring to pods
        for event in w.stream(api.list_pod_for_all_namespaces,label_selector=app_selector, timeout_seconds=0):

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
    api = client.CoreV1Api()
    #Get node pod is on and its port
    pod = api.list_pod_for_all_namespaces(field_selector="metadata.name="+pod_name).items[0]
    host_name = pod.spec.node_name
    node = api.list_node(field_selector = ("metadata.name="+host_name)).items[0]
    port = node.metadata.labels["port"]

    print(pod_name + " on " + host_name + " (" + port + ") became not ready, starting to monitor...")

    #Add pod to thread-locked queue, sleep for timeout, dequeue
    queue.enqueue(pod_name)
    time.sleep(int(timeout))
    queue.dequeue()

    print("Waited " + str(timeout) + "  seconds")

    #Try except used to catch when pods are no longer in cluster
    #This is because they properly terminated
    try:
        #Check if pod is now Ready
        #Will throw error if pod is longer around
        pod = api.list_pod_for_all_namespaces(field_selector="metadata.name="+pod_name).items[0]
        condition = get_condition(pod.status.conditions, "Ready")
        if condition is None:
            print("Ready Condtion does not exist, assume "+  pod_name + " on " + host_name + " (" + port + ") properly terminated")
        else:
            #Check if tap needs to be reconfigured
            if condition.status != "True":

                #Grab port_list and tap, reconfigure
                try:
                    port_list.remove(port)
                    tap.reconfigure(port_list.get_list())
                    print(host_name + " (" + port +  ") removed from tap: " + pod_name + " would not stay up")
                except ValueError as e:
                    print("The port " + pod_name + " was on " + host_name + " (" + port +") is already removed")
                    pass
            else:
                print(pod_name + " on " + host_name + " (" + port + ")  is now ready")


    except:
        print(pod_name +  " on " + host_name + " (" +  port + ") was terminated, no action required")
