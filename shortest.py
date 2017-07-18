import math
import requests
try:
	from lxml import etree as ET
except ImportError:
	import xml.etree.cElementTree as ET
from PIL import Image, ImageDraw
import time
import pickle
import heapq
from collections import defaultdict

import math
import requests
try:
	from lxml import etree as ET
except ImportError:
	import xml.etree.cElementTree as ET
import pickle


def osmcreate(tl=(52.4607,-1.8174),br=(52.4681,-1.8031)):
	highwaytypes='footway','cycleway','trunk','primary','secondary','tertiary','unclassified','residential','trunk_link','primary_link','secondary_link','tertiary_link','service','living_street'

	url='https://overpass-api.de/api/interpreter?data=[out:xml][timeout:25];('
	for n in highwaytypes:
		url=url+'way["highway"=\"'+n+'\"]('+str(tl[0])+','+str(tl[1])+','+str(br[0])+','+str(br[1])+');'
	url=url+');out;>;out skel qt;'
	getdata = requests.get(url)
	#with open('sampledata.pickle', 'wb') as handle:
		#pickle.dump(getdata.content, handle)
	return getdata.content


def OsmRouteImport(imported):
	'''
	returns route tree of ways ready for Dijkstra algorithm
	and dictionary of all osm nodes on ways
	'''
	root = ET.fromstring(imported)
	waydict={}
	nodes={}
	for m in root.findall('node'):
		nodes[m.attrib['id']]=[float(m.attrib['lat']),float(m.attrib['lon'])]
	for n in root.findall('way'):
		oneway=False
		for ow in n.findall('tag'):
			if ow.attrib['k']=='oneway' and ow.attrib['v']=='yes':
				pass #oneway=True. restore for one waying
		prev=None
		for l in n.findall('nd'):
			current=l.attrib['ref']
			if current not in waydict:
				waydict[current]={}
			#need to add weights in here
			if prev:
				waydict[prev][current]=distance(nodes[prev],nodes[current])
				if not oneway:
					waydict[current][prev]=distance(nodes[current],nodes[prev])
			prev=current
	#convert to format for dikstra function	
	n=[]
	for a in waydict:
		for b in waydict[a]:
			n.append([a,b,waydict[a][b]])
	return n,nodes
	
def distance(a,b):
	# approximate radius of earth in km
	R = 6373.0
	lat1 = math.radians(a[0])
	lon1 = math.radians(a[1])
	lat2 = math.radians(b[0])
	lon2 = math.radians(b[1])
	dlon = lon2 - lon1
	dlat = lat2 - lat1
	a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
	return R * c

def Dijkstra(edges,f,t):
	#returns shortest path 
	#based on: https://gist.github.com/kachayev/5990802
	shortmap=[]
	g=defaultdict(list)
	for l,r,c in edges:
		g[l].append((c,r))	
	q,seen = [(0,f,())],set()
	while q:
		(cost,v1,path)=heapq.heappop(q)
		if v1 not in seen:
			seen.add(v1)
			path = (v1,path)
			#if v1==t:return (cost,path)
			for c, v2 in g.get(v1,()):
				if v2 not in seen:
					heapq.heappush(q,(cost+c, v2, path))
					shortmap.append([v2, cost+c,cost])
	return shortmap

def findclosest(nodes,x,y):
	#finds closest nodes to location
	closest=None
	offset=float(1000000)
	for n in nodes:
		dist=distance((nodes[n][0],nodes[n][1]),(x,y))
		if dist<offset:
			offset=dist
			closest=n
	return offset,closest
	




