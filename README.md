# Python Quick Tutorial

## Table of Contents
- [Server Setup](#server)
- [Running the tutorial](#quick)
- [Generate gRPC Code](#gen)
- [Initialize the client server connection](#init)
- [Register the VRF](#vrf)
- [Add a Batch of Routes](#route)

#### <a name='server'></a>Server Setup

On the server side, we need to configure GRPC and enable the service layer through the following CLI configuration:

    ! Configure GRPC
    configure
    grpc port 57344
    grpc address-family ipv4
    commit
    end

    ! Configure Service layer
    configure
    grpc service-layer
    commit
    end


We also need to configure a server IP address. To configure an IP address on the managment interface, one can use dhcp as follows:

    ! Configure the Mgmt Interface
    configure
    interface MgmtEth 0/RP0/CPU0/0
    ipv4 address dhcp
    no shut
    commit
    end

To check the IP address assigned:

    show ip interface brief

On the client side, the very first thing we need to do is set the server IP address and gRPC port. You can check your port number by running the following CLI command on the IOS-XR server box (should be the same as the one configured):

    # show run grpc

Set the server address and port number as environment variables with the
following example command (this is assuming you are in bash shell):

    $ export SERVER_IP=192.168.122.192
    $ export SERVER_PORT=57344

The above assumes that the IP address of the node is 192.168.122.192.

This completes all the setup needed to start writing some code! Hop into
your python interpreter and try out some of the commands to get familiar
with the API.

## <a name='quick'></a>Running the tutorial

The following basic tutorial will walk you through getting started with the Service Layer API, in particular on how to add a route.
This may require some initial python and GRPC setup, which will be explained below. For now, if you already have passed this setup step, run the example:

    cd grpc/python/src
    python tutorial/quickstart.py

The following sections explain the details of the above example tutorial.

#### <a name='gen'></a>Generate gRPC Code (optional in this example)

If you are not familiar with gRPC, we recommend you refer to gRPC's
documentation before beginning with our tutorial: [gRPC Docs](http://www.grpc.io/docs/)

You should have received all of the protobuf files required to run the Cisco
Service Laye API. In order to generate the gRPC client side code stubs in python, run the following command (you may have to adjust the path to the proto files and the output according to your requirements):  

**For convenience, these files are also committed in this repo under grpc/python/src/genpy/ (so you can skip this step).**

    $ protoc -I ../../protos --python_out=. --grpc_out=./genpy/ --plugin=protoc-gen-grpc=`which grpc_python_plugin` ../../protos/*.proto

This generates the code stubs that we will now utilize to create a client.
The files are recognizable from the "_pb2" that is appended to the name of the
proto files they were generated from (example: sl_route_ipv4_pb2.py).

#### <a name='init'></a>Initialize the client server connection

In order to follow this quick tutorial, it is best to open the files in `grpc/python/src/tutorial/`

    quickstart.py  : The full tutorial example
    client_init.py : Used to setup the client-server connection
    vrf.py         : Used to setup the Route vertical

As shown in quickstart.py, the first thing to do is to setup the GRPC channel:

    server_ip, server_port = util.get_server_ip_port()
    channel = implementations.insecure_channel(server_ip, server_port)

Once connected, we need to handshake the API version number with the server.
The same RPC call also sets up an asynchronous stream of notifications from the server. The first notification would be the response to our version number message i.e. SLInitMsg, as a SLGlobalNotif event with type SL_GLOBAL_EVENT_TYPE_VERSION. This can be done by calling:

    SLGlobalInitNotif(init_msg, Timeout)

The above function takes the client major, minor and sub version numbers and sends them to the Service Layer service to get a handshake on the API version number. More on this below.

The following code snippets are copied from file client_init.py

    def client_init(stub, event):
        #
        # Create SLInitMsg to handshake the version number with the server.
        # The Server will allow/deny access based on the version number.
        # The same RPC is used to setup a notification channel for global
        # events coming from the server.
        #
        # # Set the client version number based on the current proto files' version
        init_msg = sl_global_pb2.SLInitMsg()
        init_msg.MajorVer = sl_version_pb2.SL_MAJOR_VERSION
        init_msg.MinorVer = sl_version_pb2.SL_MINOR_VERSION
        init_msg.SubVer = sl_version_pb2.SL_SUB_VERSION

        # Set a very large timeout, as we will "for ever" loop listening on
        # notifications from the server
        Timeout = 365*24*60*60 # Seconds

        # This for loop will never end unless the server closes the session
        for response in stub.SLGlobalInitNotif(init_msg, Timeout):
            if response.EventType == sl_global_pb2.SL_GLOBAL_EVENT_TYPE_VERSION:
                if (sl_common_types_pb2.SLErrorStatus.SL_SUCCESS ==
                        response.ErrStatus.Status):

The above python definition also handles other events such as errors and heartbeats.
Notice that the client_init definition above takes a GRPC stub as an argument.
This is typically created through:

    # Create the gRPC stub.
    stub = sl_global_pb2.beta_create_SLGlobal_stub(channel)

Since the above client_init function would never return, it is best to spawn it as a thread, and run it in the background. In python, we do so by calling a threading event:

    #
    # Spawn a thread for global events
    #
    def global_init(channel):
        # Create the gRPC stub.
        stub = sl_global_pb2.beta_create_SLGlobal_stub(channel)

        # Create a thread sync event. This will be used to order thread execution
        event = threading.Event()

        # The main reason we spawn a thread here, is that we dedicate a GRPC
        # channel to listen on Global asynchronous events/notifications.
        # This thread will be handling these event notifications.
        t = threading.Thread(target = global_thread, args=(stub, event))
        t.start()

#### <a name='vrf'></a>Register the VRF

In general, before we can use a vertical function like the route APIs, we have to register on that vertical. The route API allows the user to register based on a per VRF basis.
So, before any additions or modification of routes can be made we need to register with the proper VRF, which requires sending a VRF registration message and then an EOF message to clean up any stale routes that may be there from an older configuration (this will become handy on restart or recovery scenarios).

The following snippets are copied from file vrf.py

Next up, create the stub instance using the channel. This stub will
have the exact same methods that are available on the server. To do this,
we need to import the stub code generated from our ProtoBuf files. Depending on
what calls you want to make, different stubs will be used. We are going to be
making changes to our IPv4 routes, so we use the SLRoutev4Oper_stub.

    from genpy import sl_route_ipv4_pb2
    stub = sl_route_ipv4_pb2.beta_create_SLRoutev4Oper_stub(channel)

Time to fill in some variables!

Create the `SLVrfRegMsg` object. Generating a `SLVrfRegMsg` object allows us to
use dot notation to access and set it's variables.

    from genpy import sl_route_common_pb2
    vrfMsg = sl_route_common_pb2.SLVrfRegMsg()

The VRF registration message contains a set of VRF registration objects.

Create an `SLVrfReg` object.

    vrfObj = sl_route_common_pb2.SLVrfReg()

Set the VRF registration object attributes:

VRF name. The default VRF in IOS-XR is called "default":

    vrfObj.VrfName = 'default'

Administrative distance. The admin distance is used by RIB to make best path decisions.

    vrfObj.AdminDistance = 2

VRF purge interval. This is useful on restart scenarios.

    vrfObj.VrfPurgeIntervalSeconds = 500

Add the registration message to the list. In the case of a bulk object, we can
append other VRF objects to the list.

    vrfList.append(vrfObj)

Now that the list is completed, assign `vrf_list` to the `SLVrfRegMsg`.

    vrfMsg.VrfRegMsgs.extend(vrfList)

Make the RPC call.

We are ready to make our call to the API. We'll send the
`SLVrfRegMsg vrfMsg` and a timeout interval (in seconds) for the gRPC
server.

    Timeout = 10 # Seconds
    response = stub.SLRoutev4VrfRegOp(vrfMsg, Timeout)

Note that the vrfMsg has an Oper field that determines the operation type:

    SL_REGOP_REGISTER  : used for registrations
    SL_REGOP_EOF       : used for EOF signaling. Useful for restart scenarios
    SL_REGOP_UNREGISTER: used to unregister, which would clean all previous roues added in that VRF.

Finally, we can print our response from the server. Notice that, since we can add a batch of VRF registrations, we want to print a result code for each individual response.
To do this, we check if the response is an error, and if it is we print the
name of the vrf that caused the error as well as the hexadecimal error
code.

    if (response.StatusSummary.Status ==
            sl_common_types_pb2.SLErrorStatus.SL_SUCCESS):
        print "VRF %s Success!" %(
            sl_common_types_pb2.SLRegOp.keys()[oper])
    else:
        print "Error code for VRF %s is 0x%x! Response:" % (
            sl_common_types_pb2.SLRegOp.keys()[oper],
            response.StatusSummary.Status
        )
        print response
        # If we have partial failures within the batch, let's print them
        if (response.StatusSummary.Status == 
            sl_common_types_pb2.SLErrorStatus.SL_SOME_ERR):
            for result in response.Results:
                print "Error code for %s is 0x%x" %(result.VrfName,
                    result.ErrStatus.Status
                )

#### <a name='route'></a>Add a Batch of Routes

Now that we have registered the VRF, we can start adding routes. We will show
adding a batch of 10 routes to the RIB.

Create an empty list of routes.

    routeList = []

Create a `SLRoutev4Msg` message.

    rtMsg = sl_route_ipv4_pb2.SLRoutev4Msg()

Fill in the route attributes.

VRF Name

    rtMsg.VrfName = 'default'

Add a loop that will add 10 incrementing routes to the RIB table.

    for i in range(10):

Create a `SLRoutev4` object.

        route = sl_route_ipv4_pb2.SLRoutev4()

IP address
        import ipaddress
        route.Prefix = (
            int(ipaddress.ip_address('20.0.'+ str(i) + '.0'))
        )

Prefix Length

        route.PrefixLen = 24

Administrative distance (this can override the VRF registration admin distance)

        route.RouteCommon.AdminDistance = 2

Set the route's paths.

A route may have one or many paths.
Create an empty list of paths as a placeholder for these paths.

        paths = []

Create an `SLRoutePath` object.

        path = sl_route_common_pb2.SLRoutePath()

Fill in the path attributes. Note: if you are deleting a route, paths are not
required to be added, so it is better not to fill in this part for a delete.

Path next hop address

        path.NexthopAddress.V4Address = (
            int(ipaddress.ip_address('10.10.10.1'))
        )

Next hop interface name

        path.NexthopInterface.Name = 'GigabitEthernet0/0/0/0'

Add the path to the list

        paths.append(path)

Let's create another path as equal cost multi-path (ECMP)

        path = sl_route_common_pb2.SLRoutePath()
        path.NexthopAddress.V4Address = (
            int(ipaddress.ip_address('10.10.10.2'))
        )
        path.NexthopInterface.Name = 'GigabitEthernet0/0/0/0'
        paths.append(path)

Add the paths to the route object. In the example quickstart.py tutorial, we
add a line checking that the operation is not a delete operation, as we would
not need to add paths for a delete.

        if oper != sl_common_types_pb2.SL_OBJOP_DELETE:
            route.PathList.extend(paths)

Add the route to `route_list` (bulk routes)

        routeList.append(route)

Assign the `routeList` to the `rtMsg`.

    rtMsg.Routes.extend(routeList)


Make the RPC call.

    Timeout = 10 # Seconds
    rtMsg.Oper = oper # Desired ADD, UPDATE, DELETE operation
    response = stub.SLRoutev4Op(rtMsg, Timeout)

Again, in the quickstart.py tutorial we have examples of other route calls
beyond just adding bulk routes.

    # RPC route operations
    #    for add: sl_common_types_pb2.SL_OBJOP_ADD
    #    for update: sl_common_types_pb2.SL_OBJOP_UPDATE
    #    for delete: sl_common_types_pb2.SL_OBJOP_DELETE
    route_operation(channel, sl_common_types_pb2.SL_OBJOP_ADD)

These calls show examples of bulk additions, updates, and deletes

Check the server's response. Here again we can check each individual route that
was added for an error message.

    if (sl_common_types_pb2.SLErrorStatus.SL_SUCCESS == 
            response.StatusSummary.Status):
        print "Route %s Success!" %(
            sl_common_types_pb2.SLObjectOp.keys()[oper])
    else:
        print "Error code for route %s is 0x%x" % (
            sl_common_types_pb2.SLObjectOp.keys()[oper],
            response.StatusSummary.Status
        )
        # If we have partial failures within the batch, let's print them
        if (response.StatusSummary.Status == 
            sl_common_types_pb2.SLErrorStatus.SL_SOME_ERR):
            for result in response.Results:
                print "Error code for %s/%d is 0x%x" %(
                    str(ipaddress.ip_address(result.Prefix)),
                    result.PrefixLen,
                    result.ErrStatus.Status
                )

That's all for now! Remember some key takeaways:

1. The VRF must be registered before adding, updating, or removing routes
from the RIB.

2. All API operations are CRUD based (Create, Read, Update, Delete), and the initial setup of all calls to the same object will be (about) the same.
