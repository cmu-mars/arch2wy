#!/usr/local/bin/python

import yaml
import sys

def rename(x):
    return (x.replace('/','').replace('_',' ')).title().replace(' ','')

if not len(sys.argv) == 2:
    sys.exit("please provide exactly one command line argument")

with open(sys.argv[1], 'r') as stream:
    try:
        arch = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit("failed to read yaml file")

for node in arch:
    print "component " + rename(node["fullname"])
    print "\t val name: String"
    print
#    for k in node.keys():
