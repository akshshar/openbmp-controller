import yaml


class PolicyHandler(object):
    def __init__(self):
        pass


    def process_route(self, route):

        for path in route['paths']:
            if route['paths'][path]['nexthop'] == "2.2.2.2":
                route['paths'][path]['med'] = 40

        return route
