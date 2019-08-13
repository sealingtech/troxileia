Troxileia
=========

Troxileia is a Kubernetes controller that reconfigures a network tap if pods are consistently crashing on a node and/or if "sensor" label on a node is changed from true to false. Troxileia is designed to be used with sensors like Zeek, Moloch, and Suricata. It assures that the load balancing being done by the tap is consistent with the current state of the cluster.

![Picture here](trox.jpg "Troxileia")

Requirements
============

Kubernetes 14.0+

Python 3.0+ (If ran locally)

Python Kubernetes library (If ran locally)
```
pip install kubernetes
```
How to Use
==========

Troxileia can be run locally outside of the cluser or as its own pod inside the cluser. To use, all nodes need a "port" label and and nodes you intend to monitor should have a sensor label:

```
kubectl label nodes k8s-worker-1 port="1_1_x1"
kubectl label nodes k8s-worker-1 sensor="true"
```
The sensor label can be left off and added later, or initially set to false if they may be monitored later.

### To run locally:
```
python main.py
```


### To deploy as a pod in cluster in kube-system namespace:

First the variables in controller-configmap.yaml must be set.
Then the configmap must be applied to the cluser:
```
kubectl apply -f controller-configmap.yaml
```
Then to deploy:
```
kubectl apply troxileia.yaml
```
