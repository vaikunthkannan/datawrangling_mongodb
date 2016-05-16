# -*- coding: utf-8 -*-
"""
Created on Sun May 15 18:55:42 2016

@author: Vaikunth Kannan
"""

import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
from collections import defaultdict
#import pymongo
import os



OSMFILE = "santa-cruz_california.osm"
CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

#Parse through the file with ElementTree and count the number of unique element types.
def count_tags(filename):
        tags = {}
        for event, elem in ET.iterparse(filename):
            if elem.tag in tags: 
                tags[elem.tag] += 1
            else:
                tags[elem.tag] = 1
        return tags
man_tags = count_tags('santa-cruz_california.osm')
pprint.pprint(man_tags)

#pre-compiled queries
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


def key_type(element, keys):
    if element.tag == "tag":
        k = element.attrib['k']
        if lower.match(k):
            keys['lower'] = keys['lower']+1
        elif lower_colon.match(k):
            keys['lower_colon'] = keys['lower_colon']+1
        elif problemchars.match(k):
            keys['problemchars'] = keys['problemchars']+1
        else:
            keys['other'] = keys['other']+1
        pass
        
    return keys



def process_map(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys


man_keys = process_map('santa-cruz_california.osm')
pprint.pprint(man_keys)

def get_user(element):
    return


def process_mapu(filename):
    users = set()
    for _, element in ET.iterparse(filename):
        if 'uid' in element.attrib:
            users.add(element.attrib['uid'])

    return users
    
man_users = process_mapu('santa-cruz_california.osm')
pprint.pprint(len(man_users))

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


expected = ["Street", "Avenue", "Boulevard", "Broadway", "Circus", "Close", "Court", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Crescent", "Trail", "Parkway", "Commons", "Garden", "Grove", "Mount", "Park"]


mapping = {'Ave'  : 'Avenue',
           'Blvd' : 'Boulevard',
           'Dr'   : 'Drive',
           'Ln'   : 'Lane',
           'Pkwy' : 'Parkway',
           'Rd'   : 'Road',
           'Rd.'   : 'Road',
           'St'   : 'Street',
           'street' :'Street',
           'Ct'   : 'Court',
           'Cir'  : 'Circus',
           'Cr'   : 'Court',
           'ave'  : 'Avenue',
           'Sq'   : 'Square',
           'Ct'   : 'Court',
           'Gdn'  : 'Garden',
           'Gr'   : 'Grove',
           'Pl'   : 'Place',
           'Cr'   : 'Crescent',
           'Hwy'  : 'Highway',
           'Hwy.' : 'Highway'}


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types

#standardizes street types with a replacement map
def update_name(name, mapping):

    name = name.split(' ')
    type = name[-1]
    if type in mapping:
        name[-1] = mapping[type]
    
    name = ' '.join(name)

    return name
    
man_streets = audit('santa-cruz_california.osm')
pprint.pprint(dict(man_streets))
for street_type, ways in man_streets.iteritems():
    for name in ways:
        better_name = update_name(name, mapping)
        print name, "=>", better_name
        
def audit_zipcode(invalid_zipcodes, zipcode):
    twoDigits = zipcode[0:2]
    
    if not twoDigits.isdigit():
        invalid_zipcodes[twoDigits].add(zipcode)
    
    elif twoDigits != 95:
        invalid_zipcodes[twoDigits].add(zipcode)
        
def is_zipcode(elem):
    return (elem.attrib['k'] == "addr:postcode")

def audit_zip(osmfile):
    osm_file = open(osmfile, "r")
    invalid_zipcodes = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_zipcode(tag):
                    audit_zipcode(invalid_zipcodes,tag.attrib['v'])

    return invalid_zipcodes

man_zipcode = audit_zip('santa-cruz_california.osm')
pprint.pprint(dict(man_zipcode))
#update all zipcodes with replacement for proper 5 digit codes
def update_zip(zipcode):
    testNum = re.findall('[a-zA-Z]*', zipcode)
    if testNum:
        testNum = testNum[0]
    testNum.strip()
    if testNum == "CA":
        convertedZipcode = (re.findall(r'\d+', zipcode))
        if convertedZipcode:
            if convertedZipcode.__len__() == 2:
                return (re.findall(r'\d+', zipcode))[0] + "-" +(re.findall(r'\d+', zipcode))[1]
            else:
                return (re.findall(r'\d+', zipcode))[0]

for street_type, ways in man_zipcode.iteritems():
    for name in ways:
        better_name = update_zip(name)
        print name, "=>", better_name
        
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
#Converting XML to JSON
def shape_element(element):
    node = {}
    creationAttribs = ['version','changeset','timestamp','user','uid']    
    node['created'] = {}
    node['pos'] = [0,0]
    if element.tag == "way":
        node['node_refs'] = []
    if element.tag == "node" or element.tag == "way" :
        node['type'] = element.tag
        #attributes
        for k, v in element.attrib.iteritems():
            if k == 'lat':
                try:
                    lat = float(v)
                    node['pos'][0] = lat
                except ValueError:
                    pass
            elif k == 'lon':
                try:
                    lon = float(v)
                    node['pos'][1] = lon
                except ValueError:
                    pass
            elif k in creationAttribs:
                node['created'][k] = v
            else:
                node[k] = v
        #children
        for tag in element.iter('tag'):
            k = tag.attrib['k']
            v = tag.attrib['v']
            if problemchars.match(k):
                continue
            elif lower_colon.match(k):
                k_split = k.split(':')
                if k_split[0] == 'addr':
                    if 'address' not in node:
                        node['address'] = {}
                    node['address'][k_split[1]] = v
                    continue
            node[k] = v
        #way children
        if element.tag == "way":
            for n in element.iter('nd'):
                ref = n.attrib['ref']
                node['node_refs'].append(ref);
        return node
    else:
        return None



def process_map(file_in, pretty = False):
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

#p_map = process_map('santa-cruz_california.osm')



    
        
