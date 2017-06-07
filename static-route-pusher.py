import Queue
import logging.handlers
import threading
import radix

from socket import AF_INET
from grpc.beta import implementations
from netmiko import ConnectHandler
from ydk.models.cisco_ios_xr import Cisco_IOS_XR_ip_static_cfg as xr_ip_static_cfg
from ydk.providers import CodecServiceProvider
from ydk.services import CodecService

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
        self.rtQueue = Queue.Queue(maxsize=100000)
        self.poisonpillq = Queue.Queue()
        self.threadList = []
        st = []

        # self.channel = self.setup_grpc_channel()
        # self.push_routes_cli()
        self.push_routes_netconf()
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

        while appWorks:
            try:
                route = self.rtQueue.get_nowait()
                logger.info('get object')
                logger.info(route)
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

                route_event = ''

                if self.plugin.get_route_family(route) == AF_INET:
                    try:

                        # The following checks are necessary to differentiate between
                        # route add and update
                        route_check = self.plugin.is_valid_route(route)
                        if route_check['valid']:
                            route_tuple = (self.plugin.get_route_prefix(route), self.plugin.get_route_prefixlen(route))

                            batch_prefixset_v4.add(
                                (self.plugin.get_route_prefix(route), self.plugin.get_route_prefixlen(route)))

                        else:
                            commit_batch = False
                            continue
                    except Exception as e:
                        logger.debug("Failed to check if the route already exists, skip this route")
                        logger.debug("Error is " + str(e))
                        commit_batch = False
                        continue


                        # If the latest event type is different from the last event type, then
                        # create a route batch from the previous set of routes and send to RIB

                        # if route_event != rt_last_event:
                        #     # Prepare to commit the route batch now
                        #     route_batch_v4 = self.v4routeList[:]
                        #     commit_batch = True
                        #     batch_action = rt_last_event
                        #
                        #     # Cleanup for the next round of updates
                        #     self.v4routeList = []
                        #     batch_prefixset_v4.clear()
                        #
                        #     # Save the update that triggered batch creation
                        #     self.setup_v4routelist(route, route_event, route_check['type'])
                        # else:
                        #     self.setup_v4routelist(route, route_event, route_check['type'])
                        #
                        # rt_last_event = route_event
                self.rtQueue.task_done()
            finally:
                pass

    def setup_grpc_channel(self):
        logger.info("Using GRPC Server IP(%s) Port(%s)" % (self.server_ip, self.server_port))
        channel = implementations.insecure_channel(self.server_ip, self.server_port)
        # self.global_init(channel)
        # channel = implementations.insecure_channel(self.server_ip, self.server_port)
        return channel

    def push_routes_cli(self):
        xr = {
            'device_type': 'cisco_xr',
            'ip': self.server_ip,
            'username': 'vagrant',
            'password': 'vagrant',
            'port': 22,
            'secret': 'vagrant',
            'verbose': True,
        }
        net_connect = ConnectHandler(**xr)

        route_batch = ['router static address-family ipv4 unicast 11.11.11.16/32 10.1.1.20 200',
                       'router static address-family ipv4 unicast 11.11.11.17/32 10.1.1.20 200', 'commit']

        out = net_connect.send_config_set(route_batch)
        print out

    def push_routes_yang(self):
        pass

    def push_routes_netconf(self):

        xml_routes = """
        <router-static xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ip-static-cfg">
          <default-vrf>
            <address-family>
              <vrfipv4>
                <vrf-unicast>
                  <vrf-prefixes>
                    <vrf-prefix>
                      <prefix>0.0.0.0</prefix>
                      <prefix-length>0</prefix-length>
                      <vrf-route>
                        <vrf-next-hop-table>
                          <vrf-next-hop-next-hop-address>
                            <next-hop-address>172.16.1.3</next-hop-address>
                          </vrf-next-hop-next-hop-address>
                        </vrf-next-hop-table>
                      </vrf-route>
                    </vrf-prefix>
                  </vrf-prefixes>
                </vrf-unicast>
              </vrfipv4>
            </address-family>
          </default-vrf>
        </router-static>
        """

        device = {'hostname': self.server_ip,
                  'port': 22,
                  'protocol': 'ssh',
                  'username': 'vagrant',
                  'password': 'vagrant'
                  }
        # provider = NetconfServiceProvider(address=device['hostname'],
        #                                   port=device['port'],
        #                                   username=device['username'],
        #                                   password=device['password'],
        #                                   protocol=device['protocol'])
        provider = CodecServiceProvider(address=device['hostname'],
                                        port=device['port'],
                                        username=device['username'],
                                        password=device['password'],
                                        protocol=device['protocol'],
                                        type="xml")
        # Routes structure would be [{prefix : ['admin_distance', 'next_hop']}]

        # create codec service
        codec = CodecService()
        routes = [{'15.15.15.16/32': ['1', '10.1.1.10']}]
        router_static = xr_ip_static_cfg.RouterStatic()  # create object

        vrf_unicast = router_static.default_vrf.address_family.vrfipv4.vrf_unicast
        vrf_prefix = vrf_unicast.vrf_prefixes.VrfPrefix()
        for route in routes:
            for k, v in route.iteritems():

                vrf_prefix.prefix, vrf_prefix.prefix_length = k.split('/')[0], k.split('/')[1]
                vrf_next_hop_next_hop_address = vrf_prefix.vrf_route.vrf_next_hop_table.VrfNextHopNextHopAddress()
                vrf_next_hop_next_hop_address.next_hop_address = route[k][2]

                vrf_prefix.vrf_route.vrf_next_hop_table.vrf_next_hop_next_hop_address.append(vrf_next_hop_next_hop_address)
                vrf_unicast.vrf_prefixes.vrf_prefix.append(vrf_prefix)

        # encode and print object
        # print(codec.encode(provider, router_static))

        provider.close()


rtree = radix.Radix()
rnode_a = rtree.add("12.12.12.12/32")
rnode_a.data['admin_distance'] = 20
rnode_a.data['next_hop'] = '10.1.1.10'

rnode_b = rtree.add("11.11.11.11/32")
rnode_b.data['admin_distance'] = 32
rnode_a.data['next_hop'] = '10.1.1.10'

route_pusher = StaticRoutePusher(plugin='', server_ip='10.1.1.20', server_port=57344, vrf='default')


# def put_queue_value(counter):
#     while counter < 10:
#         threading.Timer(500.0, put_queue_value(counter + 1)).start()
#         route_pusher.rtQueue.put((event,))


# event = {"route": {"a_d": 20}}
#
appWorks = True
# if __name__ == '__main__':
#     try:
#         put_queue_value(5)
#     except KeyboardInterrupt:
#         appWorks = False
#         raise

# CLI
# router static address-family ipv4 unicast 11.11.11.11/32 10.1.1.20 200
