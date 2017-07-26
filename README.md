## Setup:
![setup-openbmp-controller](images/setup_openbmp_controller.png)


## Architecture
![architecture-openbmp-controller](images/architecture_openbmp_controller.png)

## Running the demo

The basic steps are as follows:

### Pre-requisites  

**Vagrant:**  

*  Have Vagrant and Virtualbox installed
*  Make sure you have access to an SL-API enabled IOS-XR vagrant box. If you don't have it get access to the IOS-XR vagrant box 
   (version = 6.1.2) by following this tutorial:  <https://xrdocs.github.io/application-hosting/tutorials/iosxr-vagrant-quickstart>

**Docker:**  

*  Install docker-ce and docker-compose  
*  Make sure you can access hub.docker.com and are able to pull images


### Steps

**Note:** You will need atleast 9G free RAM to run the vagrant + Docker topology.`

Spin up the docker topology consisting of the openbmp server + Kafka container and a kafka-slapi container:

```
git clone http://gitlab.cisco.com/akshshar/openbmp-slapi.git
cd openbmp-slapi/compose

docker-compose up -d

```

Spin up the Vagrant topology consisting of two Back-to-Back connected IOS-XR routers:

```
cd openbmp/vagrant
vagrant up

```

Once the routers come up, you can check that rtr1 is registered on the openbmp server.
Browse to:

```
http://<Your host machine IP>:db_rest/v1/routers 
```

To view the current BGP in-RIB:

```
http://<Your host machine IP>:db_rest/v1/rib
```


Finally, docker exec into the kafka_slapi container to run the client

```

cisco@pod1:~/openbmp-slapi/compose$ docker exec -it kafka_slapi bash
root@kafka-slapi:/# 
root@kafka-slapi:/# 

```

Clone the lindt-objmodel repository to fetch the python-bindings to communicate with the SL-API server on rtr1

```
root@kafka-slapi:/# 
root@kafka-slapi:~# git clone https://github.com/xrdocs-private/lindt-objmodel.git
Cloning into 'lindt-objmodel'...
Username for 'https://github.com': akshshar
Password for 'https://akshshar@github.com': 
remote: Counting objects: 229, done.
remote: Total 229 (delta 0), reused 0 (delta 0), pack-reused 229
Receiving objects: 100% (229/229), 5.03 MiB | 1.13 MiB/s, done.
Resolving deltas: 100% (106/106), done.
Checking connectivity... done.
root@kafka-slapi:~# 
```

Drop into the tutorials directory and copy over the config.yaml and consumer.py scripts from  / into the tutorials directory

```
root@kafka-slapi:~# cd lindt-objmodel/grpc/python/src/tutorial/
root@kafka-slapi:~/lindt-objmodel/grpc/python/src/tutorial# cp /config.yaml ./
root@kafka-slapi:~/lindt-objmodel/grpc/python/src/tutorial# cp /consumer.py ./

```

Now launch consumer.py and you should see the code in action:

```
root@kafka-slapi:/lindt-objmodel/grpc/python/src/tutorial# python consumer.py 
Using GRPC Server IP(192.168.122.1) Port(57777)
Global thread spawned
Server Returned 0x502, Version 0.0.0
Successfully Initialized, connection established!
Max VRF Name Len     : 33
Max Iface Name Len   : 64
Max Paths per Entry  : 128
Max Prim per Entry   : 64
Max Bckup per Entry  : 64
 

 #### SNIPPED OUTPUT ####
```


On rtr1 you should now see the routes appear as application routes:

```
RP/0/RP0/CPU0:rtr1#show route
Thu May 11 12:10:24.796 UTC

Codes: C - connected, S - static, R - RIP, B - BGP, (>) - Diversion path
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area
       N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2
       E1 - OSPF external type 1, E2 - OSPF external type 2, E - EGP
       i - ISIS, L1 - IS-IS level-1, L2 - IS-IS level-2
       ia - IS-IS inter area, su - IS-IS summary null, * - candidate default
       U - per-user static route, o - ODR, L - local, G  - DAGR, l - LISP
       A - access/subscriber, a - Application route
       M - mobile route, r - RPL, (!) - FRR Backup path

Gateway of last resort is 10.0.2.2 to network 0.0.0.0

S*   0.0.0.0/0 [1/0] via 10.0.2.2, 00:17:31, MgmtEth0/RP0/CPU0/0
L    1.1.1.1/32 is directly connected, 00:15:49, Loopback0
O    2.2.2.2/32 [110/2] via 10.1.1.20, 00:09:38, GigabitEthernet0/0/0/0
L    6.6.6.6/32 is directly connected, 00:15:49, Loopback1
C    10.0.2.0/24 is directly connected, 00:17:31, MgmtEth0/RP0/CPU0/0
L    10.0.2.15/32 is directly connected, 00:17:31, MgmtEth0/RP0/CPU0/0
C    10.1.1.0/24 is directly connected, 00:15:49, GigabitEthernet0/0/0/0
L    10.1.1.10/32 is directly connected, 00:15:49, GigabitEthernet0/0/0/0
C    11.1.1.0/24 is directly connected, 00:15:49, GigabitEthernet0/0/0/1
L    11.1.1.10/32 is directly connected, 00:15:49, GigabitEthernet0/0/0/1
a    100.1.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    100.3.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    100.4.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    100.5.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    100.6.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    100.7.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    100.8.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    100.9.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    100.10.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    100.11.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    200.1.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    200.3.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    200.4.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    200.5.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    200.6.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    200.7.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    200.8.1.0/24 [200/0] via 2.2.2.2, 00:00:32
a    200.9.1.0/24 [200/0] via 2.2.2.2, 00:00:32
RP/0/RP0/CPU0:rtr1#


```

Keep the consumer.py scripts running and play around by removing/adding routes through rtr2 BGP config and see how the "a" routes in rtr1 follow suit.
