import yaml


class PathSelection(object):
    def __init__(self):
        pass


    def process_route(self, route):

        for path in route['paths'].keys():
            if route['paths'][path]['med'] != 40:
                del route['paths'][path]
        return route
