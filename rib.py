import base64, json, os
import redis
from radix import Radix
from socket import inet_aton, inet_ntoa
import threading, Queue
from confluent_kafka import Consumer, KafkaError
import yaml, time, datetime, json, ipaddress, pdb
import ast
from routepolicy import PolicyHandler
from pathselection import PathSelection

import logging, logging.handlers
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)



class RIB(object):
    def __init__(self):
        self.radixRib = Radix()

    def serialize(self):
        '''To encode the py-radix object, we'll convert into a dictionary'''

        # The py-radix object contains all the prefixes and associated metadata for 
        # each prefix in a single py-radix object. Convert this into a nested dict.
        rib = []

        # walk through the current list of nodes in the tree
        nodes = self.radixRib.nodes()
        for node in nodes:
            entry = {}
            entry["family"] = node.family
            entry["network"] = node.network
            entry["prefix"] = node.prefix
            entry["prefix_len"] = node.prefixlen
            entry["paths"] = node.data
            rib.append(entry)

        return rib


    def process_msg(self, route):
        # Start processing the individual routes Received

        addr = inet_aton(str(route['prefix']))
        logger.debug("Received route with prefix = "+str(route['prefix'])+"/"+str(route['prefix_len'])+" and action="+str(route['action']))
        ribnode = self.radixRib.search_exact(packed = addr, masklen = int(route['prefix_len']))
        if ribnode is None:
            # Particular prefix/prefix-len does not exist in tree, create the node
            ribnode = self.radixRib.add(packed = addr, masklen = int(route['prefix_len']))

            # Create a dictionary with only the path information and path hash as the key
            for key in ['prefix', 'prefix_len']:
                del route[key]

            path_hash = route['hash']
            del route['hash']

            route_paths = { str(path_hash) : route }

            # add the path to the route path dictionary
            ribnode.data.update(route_paths)
            logger.debug("Added the path to the route entry, path hash="+path_hash)
        else:
            #Particular prefix/prefix-len already exists in tree, update the path based on action
            # Create a dictionary with only the path information and path hash as the key
            for key in ['prefix', 'prefix_len']:
                del route[key]

            path_hash = route['hash']
            del route['hash']

            # if action == add, update the existing path
            # if action == del, delete the existing path

            if route["action"] == "del":
                if path_hash in ribnode.data:
                    del ribnode.data[path_hash]
                    logger.debug("path deleted from tree, hash="+path_hash)
                else:
                    logger.debug("Delete for a path that did not exist already")
            elif route["action"] == "add":
                route_paths = { str(path_hash) : route }
                ribnode.data.update(route_paths)
                logger.debug("Path added to the tree, hash="+path_hash)



class AdjRibPostPolicy(RIB):

    def __init__(self ):
        self.radixRib = Radix()
        self.policy  = PolicyHandler()

    def process_adjInRib(self, node_hash, redisClient):
        # Got an event for the node, obtain the current RIB from redis based off node hash
        adjInRib = ast.literal_eval(redisClient.hget(node_hash, 'adjInRib'))

        if adjInRib:
           for route in adjInRib:
               route = self.policy.process_route(route)
               ribnode = self.radixRib.search_exact(str(route['prefix']))
        
               if ribnode is None:
                   # Particular prefix/prefix-len does not exist in tree, create the node
                   ribnode = self.radixRib.add(str(route['prefix']))

                   # Create a dictionary with only the path information and path hash as the key
                   for key in ['prefix', 'prefix_len']:
                       del route[key]

                   ribnode.data.update(route['paths'])
                
               else:
                   #Particular prefix/prefix-len already exists in tree, update the path based on action
                   # Create a dictionary with only the path information and path hash as the key
                   for key in ['prefix', 'prefix_len']:
                       del route[key]
                   ribnode.data.update(route['paths'])
          
           
class LocalRib(RIB):

    def __init__(self ):
        self.radixRib = Radix()
        self.pathselection  = PathSelection()

    def process_adjInRibPP(self, node_hash, redisClient):
        # Got an event for the node, obtain the current RIB from redis based off node hash
        print redisClient.hget(node_hash, 'adjInRibPP')
        adjInRibPP = ast.literal_eval(redisClient.hget(node_hash, 'adjInRibPP'))
        if adjInRibPP:
           for route in adjInRibPP:
               print "route from AdjInRibPP ="
               print route
               route = self.pathselection.process_route(route)
               print "route for localrib = "
               print route
               ribnode = self.radixRib.search_exact(str(route['prefix']))

               if ribnode is None:
                   # Particular prefix/prefix-len does not exist in tree, create the node
                   ribnode = self.radixRib.add(str(route['prefix']))

                   # Create a dictionary with only the path information and path hash as the key
                   for key in ['prefix', 'prefix_len']:
                       del route[key]

                   ribnode.data.update(route['paths'])

               else:
                   #Particular prefix/prefix-len already exists in tree, update the path based on action
                   # Create a dictionary with only the path information and path hash as the key
                   for key in ['prefix', 'prefix_len']:
                       del route[key]
                   ribnode.data.update(route['paths'])

