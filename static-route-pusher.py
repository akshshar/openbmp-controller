# from grpc_cisco.grpcClient import CiscoGRPCClient
# from grpc_cisco import ems_grpc_pb2
import radix



import Queue, threading
from socket import AF_INET
import logging, logging.handlers
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class StaticRoutePusher:
    def __init__(self, plugin, vrf, server_ip, server_port):

        self.server_ip = server_ip
        self.server_port = server_port

        self.vrf = vrf
        self.v4routeList = []
        self.plugin = plugin
        self.rtQueue= Queue.Queue(maxsize=100000)
        self.poisonpillq = Queue.Queue()
        self.threadList = []
        st = []

        self.channel = self.setup_grpc_channel()
        for fn in [self.route_batch]:
            thread = threading.Thread(target=fn, args=())
            self.threadList.append(thread)
            thread.daemon = True
            thread.start()

    def route_batch(self, batch_size=100000):

        route_batch_v4 = []
        rt_last_event = 'add'  # Possible values include add, update, delete
        batch_prefixset_v4 = set()
        commit_batch = False
        route = None

        while True:
            try:
                route = self.rtQueue.get_nowait()
            except Queue.Empty:
                # Used to initiate a batch commit when queue become empty
                commit_batch = True
                if self.v4routeList:
                    route_batch_v4 = self.v4routeList[:]
                    self.v4routeList = []
                    batch_action = rt_last_event
            else:
                logger.debug("Got a Route Message!")
                logger.debug(route)

                if isinstance(route, str) and route == "quit":
                    logger.debug("Quitting the route worker thread")
                    break

                try:
                    logger.debug(self.plugin.get_route_prefix(route))
                except:
                    logger.debug("No prefix in route")

                route_event = ''

                if self.plugin.get_route_family(route) == AF_INET:
                    try:
                        # The following checks are necessary to differentiate between
                        # route add and update

                        route_check = self.plugin.is_valid_route(route)
                        if route_check['valid'] :
                            route_tuple = (self.plugin.get_route_prefix(route),self.plugin.get_route_prefixlen(route))
                            response, verdict = self.prefix_in_rib(route)

                            # Check if the route is already present in application RIB
                            # or if the route is present in the current batch itself
                            if (verdict or
                                        route_tuple in batch_prefixset_v4):
                                if self.plugin.route_events[route['event']] == 'add':
                                    route_event = 'update'
                                else:
                                    route_event = self.plugin.route_events[route['event']]
                            else:
                                route_event = self.plugin.route_events[route['event']]

                            batch_prefixset_v4.add((self.plugin.get_route_prefix(route), self.plugin.get_route_prefixlen(route)))

                        else:
                            commit_batch = False
                            continue
                    except Exception as e:
                        logger.debug("Failed to check if the route already exists, skip this route")
                        logger.debug("Error is " +str(e))
                        commit_batch = False
                        continue


                    # If the latest event type is different from the last event type, then
                    # create a route batch from the previous set of routes and send to RIB

                    if route_event != rt_last_event:
                        # Prepare to commit the route batch now
                        route_batch_v4 = self.v4routeList[:]
                        commit_batch = True
                        batch_action = rt_last_event

                        # Cleanup for the next round of updates
                        self.v4routeList = []
                        batch_prefixset_v4.clear()

                        # Save the update that triggered batch creation
                        self.setup_v4routelist(route, route_event, route_check['type'])
                    else:
                        self.setup_v4routelist(route, route_event, route_check['type'])

                    rt_last_event = route_event
                self.rtQueue.task_done()
            finally:
                if route_batch_v4:
                    logger.debug("Current commit batch: " +str(commit_batch))
                    if commit_batch:
                        logger.debug("Current route batch:")
                        logger.debug(route_batch_v4)

                        # Batch action to push routes and type of action
                        # self.rtbatch_send(route_batch_v4, batch_action)

                        route_batch_v4= []
                        commit_batch = False
                        route = None

    def push_routes_yang(self):
        pass


rtree = radix.Radix()
rnode_a = rtree.add("12.12.12.12/32")
rnode_a.data['admin_distance'] = 20
rnode_a.data['next_hop'] = '10.1.1.10'

rnode_b = rtree.add("11.11.11.11/32")
rnode_b.data['admin_distance'] = 32
rnode_a.data['next_hop'] = '10.1.1.10'

# CLI
# router static address-family ipv4 unicast 11.11.11.11/32 10.1.1.20 200




