import base64, json, os
import redis
from radix import Radix
from socket import inet_aton, inet_ntoa
import threading, Queue
from confluent_kafka import Consumer, KafkaError
import yaml, time, datetime, json, ipaddress, pdb

import logging, logging.handlers
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class RedisRib(object):
    '''
    A base object backed by redis.
    We will convert our radix tree based structure into json to store in Redis
    for easy retrieval by external users and to isolate between threads.
    '''

    def __init__(self, redishost = None, id = None):
        '''Create or load a RedisObject. The id is the key for the redis entry.
        For our RIB this ID will be the neighbor that the RIB corresponds to.'''

        self.redis = redis.StrictRedis(host=redishost, decode_responses = True)

        if id:
            self.id = id
        else:
            self.id = base64.urlsafe_b64encode(os.urandom(9)).decode('utf-8')

        if ':' not in self.id:
            self.id = self.__class__.__name__ + ':' + self.id

    def __bool__(self):
        '''Test if an object currently exists'''

        return self.redis.exists(self.id)

    def __eq__(self, other):
        '''Tests if two redis objects are equal (they have the same key)'''

        return self.id == other.id

    def __str__(self):
        '''Return this object as a string for testing purposes.'''

        return self.id

    def delete(self):
        '''Delete this object from redis'''

        self.redis.delete(self.id)


    def encode_value(self, value):
        '''To encode the incoming py-radix object, we'll convert into a json format'''

        # The py-radix object coming in contains all the prefixes and associated metadata
        # for each prefix in a single py-radix object. Convert this into a nested dict.
        rib = []

        # walk through the current list of nodes in the tree
        nodes = value.nodes()
        for node in nodes:
            entry = {}
            entry["family"] = node.family
            entry["network"] = node.network
            entry["prefix"] = node.prefix
            entry["prefix_len"] = node.prefixlen
            entry["attributes"] = node.data
            rib.append(entry)

        return json.dumps(rib)


    def decode_value(self, value):
        '''Convert the json object back to pyradix for quick handling of prefix matches'''

        ribtree = Radix()

        try:
            rib = json.loads(value)
        except ValueError, e:
            logger.debug("Invalid json, returning None")
            return None

        try:
            for entry in rib:
                ribnode = ribtree.add(str(entry['prefix']))
                ribnode.data.update(entry["attributes"])
        except Exception as e:
            logger.debug("Error while accessing the rib, error is "+str(e))

        return ribtree


    def get(self, key):
        '''
        Load a field from this redis object.
        '''

        return self.decode_value(self.redis.hget(self.id, key))

    def set(self, key, val):
        '''
        Store a value in this redis object.
        '''

        self.redis.hset(self.id, key, self.encode_value(val))




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
            entry["attributes"] = node.data
            rib.append(entry)

        logger.debug("Serializing the RIB")
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
            route_attrs = { path_hash : route }

            # add the path to the route attributes
            ribnode.data.update(route_attrs)
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
                route_attrs = { path_hash : route }
                ribnode.data.update(route_attrs)
                logger.debug("Path added to the tree, hash="+path_hash)



class AdjRibPostPolicy(RIB):

    def apply_policy(self):
       # Perform modification operations on the individual knobs in each
       # as instructed by the user
        pass

    def process_msg(self):
       # Invoked through pub-sub via Redis
        pass


class LocalRib(RIB):

    def path_selection(self):

        pass

    def process_msg(self):
    # Invoked through pub-sub via Redis
        pass


