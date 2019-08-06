# troxileia
troxileia WIP

Troxileia is a Kubernetes controller that will reconfigure a network tap that is distributing traffic to sensors based on if a node is set to be used as a sensor.

Troxilea works in a Kubernetes Cluster that labels nodes with {sensor:true/false} and {port:bid_sid_pid}. The port label is used in Kubernetes to note which port number the node is conencted to on the tap. The sensor label is used to designate if a note is to be used as a sensor. If the sensor label is completely absent, it is evaluated to be sensor=false.
