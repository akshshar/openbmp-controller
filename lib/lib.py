# Author Rupesh Patro
import yaml
import json


def parameters_conversion(yaml_file, json_file):
    with open(yaml_file, 'r') as stream:
        yaml_if_condition = yaml.load(stream)

    with open(json_file, 'r') as jsonstream:
        json_dict = json.load(jsonstream)

    attributes = json_dict.get('attributes')

    if attributes:
        try:
            yaml_if_condition.get('match_peerip')
        except KeyError:
            return "No match_peerip is provided in yaml file"
        for an_ip in yaml_if_condition.get('match_peerip'):
            for ip, ip_value in an_ip.items():
                values_to_change = ip_value.get('action')
                if not values_to_change:
                    return "No action stated for match_peerip"
                med_to_change = values_to_change.get('med')
                local_pref_to_change = values_to_change.get('local_pref')
                for hsh, attribute_value in attributes.items():
                    if ip in attribute_value.get('peer_ip'):
                        if med_to_change:
                            attribute_value.update({'med': med_to_change})
                        if local_pref_to_change:
                            attribute_value.update({'local_pref': local_pref_to_change})
    else:
        raise KeyError('No attribute is present in the json file provided')

    json_dict.update({'attributes': attributes})
    jsonarray = json.dumps(json_dict, indent=4, ensure_ascii=False)
    return json_dict


test_yaml = """
match_peerip: 
 - 2.2.2.2:
    action:
     med: 10
     local_pref: 30
 - 11.1.1.20:
    action:
     med: 20
     local_pref: 40
"""
test_json = {
    "attributes": {
        "45375a0b675975dd690d95a75d83c8d3": {
            "action": "add",
            "aggregator": "",
            "as_path": "",
            "as_path_count": 0,
            "base_attr_hash": "0d3c02daf122c5b3ebf8c2d5668c0112",
            "cluster_list": "",
            "community_list": "",
            "ext_community_list": "",
            "isAdjRibIn": 1,
            "isAtomicAgg": 0,
            "isIPv4": 1,
            "isNexthopIPv4": 1,
            "isPrePolicy": 1,
            "labels": "",
            "local_pref": 200,
            "med": 0,
            "nexthop": "2.2.2.2",
            "origin": "igp",
            "origin_as": 0,
            "originator_id": "",
            "path_id": 0,
            "peer_asn": 65000,
            "peer_hash": "188cf72dd6505e4ccbfd250445ce5c4f",
            "peer_ip": "2.2.2.2",
            "router_hash": "c56907838e4bd21c731491eff5f3f262",
            "router_ip": "12.1.1.10",
            "seq": 5,
            "timestamp": 1496569372000
        },
        "bd166dfec444b0e7d6cc69fab50d26d6": {
            "action": "add",
            "aggregator": "",
            "as_path": " 65001",
            "as_path_count": 1,
            "base_attr_hash": "08dc3bc601a180044c7bd838a3bf2a60",
            "cluster_list": "",
            "community_list": "",
            "ext_community_list": "",
            "isAdjRibIn": 1,
            "isAtomicAgg": 0,
            "isIPv4": 1,
            "isNexthopIPv4": 1,
            "isPrePolicy": 1,
            "labels": "",
            "local_pref": 0,
            "med": 0,
            "nexthop": "11.1.1.20",
            "origin": "igp",
            "origin_as": 65001,
            "originator_id": "",
            "path_id": 0,
            "peer_asn": 65001,
            "peer_hash": "0c0730c88306d151f91479a2374cfc55",
            "peer_ip": "11.1.1.20",
            "router_hash": "c56907838e4bd21c731491eff5f3f262",
            "router_ip": "12.1.1.10",
            "seq": 34,
            "timestamp": 1496569390000
        }
    },
    "family": 2,
    "network": "200.4.1.0",
    "prefix": "200.4.1.0/24",
    "prefix_len": 24
}
