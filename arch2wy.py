#!/usr/local/bin/python

import yaml
import sys

def titlecase(x):
    return (x.replace('/','').replace('_',' ')).title().replace(' ','')

def afterslash(x):
    ## this is really brittle
    return x.split('/')[1]

if not len(sys.argv) == 3:
    sys.exit("please provide exactly two command line arguments: the yaml file and the desired name for the architecture")

with open(sys.argv[1], 'r') as stream:
    try:
        arch = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit("failed to read yaml file")

components = []

for node in arch:
    print "component " + titlecase(node["fullname"])
    components.append(titlecase(node["fullname"]))
    print "\tval name: String"
    ## todo pubs go here, pending chris adding them to the yaml file
    for s in node["subs"]:
        print "\tport " + (s["name"].replace('/','')) + "_sub: provides " \
               + afterslash(s["format"]) + "IFace"
    print


# todo: are these always in every architecture? surely not, but i don't see
# how they derive from the yaml; Tf is mentioned but ROS topics aren't
# explicitly.
print "connector ROS1Topic"
print "\tval name: String"
print
print "connector ROS1Tf"

print
print "architecture " + sys.argv[2]
print "\tcomponenets"

index = 0
for c in components:
    print "\t\t" + c + " c" + str(index) ## todo: no idea how to get good names for these
    index = index + 1

    #todo: traversing the file above we should be able to build a
    #dictionary of connector names mapping to names of things that use them
    #and possibly attributes as well. that woul resolve the todo above
    #about connectors as well. i do not see that information in the yaml
    #file now. but if we had it, it'd be easy to walk over that and produce
    #the two lines here.
    #
    # the subs are one source of connector, but for instance i don't know
    # how to go from
    #
    # - format: geometry_msgs/Twist
    #    name: /cmd_vel
    #
    # to knowing that cmd_vel is a ROS1Topic. that identifier comes out of
    # thin air a bit.
