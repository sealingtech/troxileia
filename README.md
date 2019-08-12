# troxileia
troxileia WIP

Troxileia is a Kubernetes controller written in Python that will reconfigure a network tap distributing traffic to sensors.

Troxilea works in a Kubernetes Cluster that labels nodes with {sensor:true/false} and {port:bid_sid_pid}. The port label is used in Kubernetes to note which port number the node is conencted to on the tap. The sensor label is used to designate if a note is to be used as a sensor. If the sensor label is completely absent, it is evaluated to be sensor=false.


On the Kubernetes side, Troxileia uses two controllers. The first, sensor_controller, works by using a Kubernetes watch object to track changes to nodes. When starting up, Troxlieia stores the name of all nodes in the cluster with their corresponding value of the label sensor in a dictionary. The watch object is then used to track Kubernetes events related to nodes. The controller watches only events that modified the node, and checks if the current value of sensor is different than the previously known state of sensor stored in the dictionary. If it is different, it updates the dictionary, creates a list of port numbers stored in the port label of all nodes with the label sensor=true, and then reconfigures the tap to use these ports with the sensors. 


The second controller, pod_controller, watches for when a pod's status of Ready becomes not True. In the configmap, the app label to watch and the timeout to wait for is specified. The timeout is how long to wait once it is seen that a pod becomes not ready. The controller will create another thread, and check if that pod is ready after the timeout.


These two controllers run concurently as two seperate threads split off from a main thread that contains thread locked variables of port_list and tap. Troxileia uses a config-map to store the ip, username, and password for the network tap, the timeout to wait for pods, and the app_label of pods to watch. These are created and accessed as environmental variables inside the pod.


Troxileia is currently only compatible with Gigamon Gigavue network taps. Communication to the tap is done through SSH because the Gigavue API resides on a VM. Reconfiguration of the tap consists of deleting the current map, deleting the current Gigastream port-group, creating a new Gigastream port-group, and then creating a new map.

To function with a Kubernetes cluser, use of a sensor label and port label are required in the form of:

sensor="true" or sensor"false"

port="1_1_x1" for a port 1/1/x1
