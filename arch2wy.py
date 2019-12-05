#!/usr/local/bin/python

from enum import Enum

import os
import sys
import yaml

PortKind = Enum('PortKind', 'PROVIDES REQUIRES')

class ComponentTypeInfo:
    def __init__(self, typename, portset):
        self.typename = typename
        self.portset = portset
        # IMPLEMENTATION: Ignoring port names for checking if two
        #                 component types are same
        # Dictionary that maps provides port interfaces to their counts
        #self.provides_interfaces_to_count = {}
        # Dictionary that maps requires port interfaces to their counts
        #self.requires_interfaces_to_count = {}
        #for p in self.portset:
        #    if p.kind == PortKind.PROVIDES:
        #        if self.provides_interfaces_to_count.get(p.interface):
        #            self.provides_interfaces_to_count[p.interface] += 1
        #        else:
        #            self.provides_interfaces_to_count[p.interface] = 1
        #    elif p.kind == PortKind.REQUIRES:
        #        if self.requires_interfaces_to_count.get(p.interface):
        #            self.requires_interfaces_to_count[p.interface] += 1
        #        else:
        #            self.requires_interfaces_to_count[p.interface] = 1
        #    else:
        #        raise ValueError('Unknown port kind')

    def __eq__(self, rhs):
        # IMPLEMENTATION: Ignoring port names for checking if two
        #                 component types are same
        #return self.provides_interfaces_to_count == rhs.provides_interfaces_to_count \
        #       and self.requires_interfaces_to_count == rhs.requires_interfaces_to_count

        # FIXME: Ideally, the name of the ports shouldn't matter. This is true
        #        in the case of ROS systems, at least. But correctly implementing
        #        this would require port name rewriting for component instances.
        #        I would like to see some example in practice before implementing
        #        it.
        return self.portset == rhs.portset

    #def __key__(self):
    #    # IMPLEMENTATION: Ignoring port names for checking if two
    #    #                 component types are same
    #    # FIXME: It probably makes sense to move this to the constructor
    #    #        but we aren't worried about performance at this point.
    #    return tuple(sorted(self.provides_interfaces_to_count.items())) \
    #           + tuple(sorted(self.requires_interfaces_to_count.items()))

    def __hash__(self):
        # IMPLEMENTATION: Ignoring port names for checking if two
        #                 component types are same
        #return hash(self.__key__())
        return hash(frozenset(self.portset))

class PortInfo:
    def __init__(self, name, kind, interface):
        self.name = name
        self.kind = kind
        self.interface = interface

    def __eq__(self, rhs):
        return self.name == self.name \
               and self.kind == rhs.kind \
               and self.interface == rhs.interface

    def __key__(self):
        return (self.name, self.kind, self.interface)

    def __hash__(self):
        # Not the fastest way to implement this but we are not
        # worried about performance at this point.
        return hash(self.__key__())

def titlecase(x):
    return (x.replace('/','').replace('_',' ')).title().replace(' ','')

def afterslash(x):
    ## this is really brittle
    return x.split('/')[1]

num_args = len(sys.argv)
if num_args != 3 and num_args != 4:
    sys.exit("Usage: python arch2wy.py <Path to YAML file> <Architecture name> [<Output directory>]")

with open(sys.argv[1], 'r') as stream:
    try:
        arch = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit("failed to read yaml file")

# Dictionary that maps component types to their names
component_types_to_typenames = {}

# Dictionary that maps components to their types
#components_to_types = {}

# List of components
components = []

# Dictionary that maps component types to components
component_types_to_components = {}

# Dictionary that maps topics to the ports that they connect together
topics_to_ports = {}

# List of ports that are connected by the tf topic
tf_ports = []

# List of ports that are connected by the tf_static topic
tf_static_ports = []

for node in arch:
    component_type_name = titlecase(node["kind"])
    component_name = node["fullname"].replace("/", "")
    components.append(component_name)

    portset = set()
    for p in node["pubs"]:
        topic_name = p["name"].replace("/", "")
        portname = topic_name + "_pub"
        interface = afterslash(p["format"]) + "Iface"
        portset.add(PortInfo(portname, PortKind.REQUIRES, interface))
        if topic_name == "tf":
            tf_ports.append(component_name + "." + portname)
        elif topic_name == "tf_static":
            tf_static_ports.append(component_name + "." + portname)
        else:
            if topics_to_ports.get(topic_name):
                topics_to_ports[topic_name].append(component_name + "." + portname)
            else:
                topics_to_ports[topic_name] = [ component_name + "." + portname ]

    for p in node["subs"]:
        topic_name = p["name"].replace("/", "")
        portname = topic_name + "_sub"
        interface = afterslash(p["format"]) + "Iface"
        portset.add(PortInfo(portname, PortKind.PROVIDES, interface))
        if topic_name == "tf":
            tf_ports.append(component_name + "." + portname)
        elif topic_name == "tf_static":
            tf_static_ports.append(component_name + "." + portname)
        else:
            if topics_to_ports.get(topic_name):
                topics_to_ports[topic_name].append(component_name + "." + portname)
            else:
                topics_to_ports[topic_name] = [ component_name + "." + portname ]

    component_type = ComponentTypeInfo(component_type_name, portset)

    component_types_to_typenames[component_type] = component_type_name
    #components_to_types[component_name] = component_type
    if component_types_to_components.get(component_type):
        component_types_to_components[component_type].append(component_name)
    else:
        component_types_to_components[component_type] = [ component_name ]

output_dir = ""
if num_args == 4:
    output_dir = output_dir + sys.argv[3]

cnc_file_path = os.path.join(output_dir, sys.argv[2] + ".wyc")
with open(cnc_file_path, 'w') as cnc:
    for component_type in component_types_to_typenames:
        cnc.write("component " + component_types_to_typenames[component_type] + "\n")
        cnc.write("\tval name: String\n")
        for port in component_type.portset:
            cnc.write("\tport " + port.name + ": ")
            if port.kind == PortKind.PROVIDES:
                cnc.write("provides ")
            elif port.kind == PortKind.REQUIRES:
                cnc.write("requires ")
            else:
                raise ValueError('Unknown port kind')
            cnc.write(port.interface)
            cnc.write("\n")

        cnc.write("\n")

    if topics_to_ports:
        cnc.write("connector ROS1Topic\n")
        cnc.write("\tval name: String\n\n")

    if tf_ports or tf_static_ports:
        cnc.write("connector ROS1Tf\n")
        cnc.write("\tval is_static: Boolean\n\n")

    cnc.write("architecture " + sys.argv[2] + "\n")
    cnc.write("\tcomponents\n")
    for component_type in component_types_to_components:
        cnc.write("\t\t" + component_types_to_typenames[component_type] + " ")

        component_list = component_types_to_components[component_type]
        cnc.write(", ".join(component_list))
        cnc.write("\n")

    cnc.write("\n")

    cnc.write("\tconnectors\n")

    if topics_to_ports:
        cnc.write("\t\tROS1Topic ")
        cnc.write(", ".join(topics_to_ports.keys()))
        cnc.write("\n")

    tf_topics = []
    if tf_ports:
        tf_topics.append("tf")

    if tf_static_ports:
        tf_topics.append("tf_static")

    if tf_topics:
        cnc.write("\t\tROS1Tf ")
        cnc.write(", ".join(tf_topics))
        cnc.write("\n")

    cnc.write("\n")

    cnc.write("\tattachments\n")

    for topic in topics_to_ports:
        ports = topics_to_ports[topic]
        cnc.write("\t\tconnect ")
        cnc.write(" and ".join(ports))
        cnc.write(" with " + topic + "\n")

    if tf_ports:
        cnc.write("\t\tconnect ")
        cnc.write(" and ".join(tf_ports))
        cnc.write(" with tf\n")

    if tf_static_ports:
        cnc.write("\t\tconnect ")
        cnc.write(" and ".join(tf_static_ports))
        cnc.write(" with tf_static\n")

deployment_file_path = os.path.join(output_dir, sys.argv[2] + ".wyd")
with open(deployment_file_path, 'w') as deploy:
    deploy.write("deployment " + sys.argv[2] + "Deployment extends " + sys.argv[2] + "\n")

    for component in components:
        deploy.write("\t" + component + ".name = \"" + component + "\"\n")

    deploy.write("\n")

    for topic in topics_to_ports:
        deploy.write("\t" + topic + ".name = \"" + topic + "\"\n")

    deploy.write("\n")

    if tf_ports:
        deploy.write("\ttf.is_static = false\n")

    if tf_static_ports:
        deploy.write("\ttf_static.is_static = true\n")
