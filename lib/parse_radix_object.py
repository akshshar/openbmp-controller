import radix
from collections import defaultdict


def get_prefix_info(node):
    '''
    Given a radix node ( object)
    Returns a dictionary radix_prefix_info[prefix] = [admin_distance, next-hop]
    '''
    prefix_info = defaultdict(list)
    if not node:
        return prefix_info
    try:
        prefix_info[node.prefix].append(node.data['admin_distance'])
        prefix_info[node.prefix].append(node.data['next-hop'])
    except (ValueError,KeyError):
        print('Hit exception getting info')
        return prefix_info
    return prefix_info
