#!/usr/bin/env python3

import argparse
import json
import math
import random
import xml.etree.ElementTree

def parse_nodes(xgmml, names):
	idmap = {}
	nodes = []
	for xgmmlnode in xgmml:
		attrib = xgmmlnode.attrib
		if 'id' in attrib:
			idmap[attrib['id']] = len(nodes)
			attrib = xgmmlnode.find('{http://www.cs.rpi.edu/XGMML}graphics').attrib
			node = {}
			node['x'] = float(attrib['x'])
			node['y'] = float(attrib['y'])
			node['z'] = float(attrib['z'])
			if 'fill' in attrib:
				node['color'] = attrib['fill']
			node['name'] = xgmmlnode.find('./{http://www.cs.rpi.edu/XGMML}att[@name="%s"]' % names).get('value')
			nodes.append(node)
	return idmap, nodes

def parse_edges(xgmml, idmap):
	edges = []
	for xgmmledge in xgmml:
		attrib = xgmmledge.attrib
		if 'source' in attrib and 'target' in attrib and attrib['source'] in idmap and attrib['target'] in idmap:
			edge = {}
			edge['source'] = idmap[attrib['source']]
			edge['target'] = idmap[attrib['target']]
			attrib = xgmmledge.find('{http://www.cs.rpi.edu/XGMML}graphics').attrib
			if 'fill' in attrib:
				edge['color'] = attrib['fill']
			edges.append(edge)
	return edges

def read_xgmml(filename, names):
	idmap = {}
	network = {}
	xgmmlroot = xml.etree.ElementTree.parse(filename).getroot()
	idmap, network['nodes'] = parse_nodes(xgmmlroot.findall('{http://www.cs.rpi.edu/XGMML}node'), names)
	network['edges'] = parse_edges(xgmmlroot.findall('{http://www.cs.rpi.edu/XGMML}edge'), idmap)
	return network

def center_network(network):
	xmin = xmax = network['nodes'][0]['x']
	ymin = ymax = network['nodes'][0]['y']
	for node in network['nodes']:
		x = node['x']
		y = node['y']
		if x < xmin:
			xmin = x
		if x > xmax:
			xmax = x
		if y < ymin:
			ymin = y
		if y > ymax:
			ymax = y
	xoffset = (xmin+xmax)/2.0
	yoffset = (ymin+ymax)/2.0
	for node in network['nodes']:
		node['x'] = node['x']-xoffset
		node['y'] = node['y']-yoffset

def create_network_depth(network, depth):
	zmin = zmax = network['nodes'][0]['z']
	for node in network['nodes']:
		z = node['z']
		if z < zmin:
			zmin = z
		if z > zmax:
			zmax = z
	if zmin == zmax:
		for node in network['nodes']:
			node['z'] = random.uniform(0, depth)
	else:
		for node in network['nodes']:
			node['z'] = depth*(z-zmin)/(zmax-zmin)

def scale_network_circle(network, scale):
	d_max = 0.0
	for node in network['nodes']:
		d = node['x']**2.0+node['y']**2.0
		if d > d_max:
			d_max = d
	factor = math.sqrt(d_max)/scale
	for node in network['nodes']:
		node['x'] = node['x']/factor
		node['y'] = node['y']/factor

def scale_network_rectangle(network, aspect):
	scale = 0.0
	for node in network['nodes']:
		x = abs(node['x'])
		y = abs(node['y'])*aspect
		d = x if x >= y else y
		if d > scale:
			scale = d
	for node in network['nodes']:
		node['x'] = node['x']/scale
		node['y'] = node['y']/scale 

def project_network_hemisphere(network, radius):
	for node in network['nodes']:
		x = node['x']
		y = node['y']
		z = node['z']
		h = x**2.0+y**2.0
		r = radius-z
		node['x'] = r*2.0*x/(h+1.0)
		node['y'] = r*(1.0-h)/(h+1.0)
		node['z'] = -r*2.0*y/(h+1.0) 

def project_network_floor(network, radius):
	for node in network['nodes']:
		x = node['x']
		y = node['y']
		z = node['z']
		node['x'] = radius*x
		node['y'] = z
		node['z'] = -radius*y

def project_network_wall(network, radius):
	for node in network['nodes']:
		x = node['x']
		y = node['y']
		z = node['z']
		r = radius-z
		node['x'] = r*math.sin(math.pi*x)
		node['y'] = math.pi*radius*y+1.0
		node['z'] = -r*math.cos(math.pi*x)

def write_html(prefix, network, ar, dark, nodesize, radius):
	color1 = '#FFFFFF'
	color2 = '#F0F0F0'
	color3 = '#000000'
	if dark:
		color1 = '#000000'
		color2 = '#0F0F0F'
		color3 = '#FFFFFF'
	names = []
	positions = []
	for node in network['nodes']:
		names.append('"%s"' % node['name'])
		positions.append('%.6f' % node['x'])
		positions.append('%.6f' % node['y'])
		positions.append('%.6f' % node['z'])
	f = open(prefix+'.html', 'w')
	try:
		f.write('<!DOCTYPE html>\n<html>\n')
		f.write('  <head>\n')
		f.write('    <script src="aframe-master.min.js"></script>\n')
		f.write('    <script src="aframe-network-component.js"></script>\n')
		f.write('    <script>\n')
		f.write('      AFRAME.registerComponent("look-at", {schema: {type: "selector"}, init: function () {}, tick: function () {this.el.object3D.lookAt(this.data.object3D.position);}});\n')
		f.write('    </script>\n')
		f.write('  </head>\n')
		f.write('  <body>\n')
		f.write('    <audio id="audioOn" src="click_on.wav"></audio>\n')
		f.write('    <audio id="audioOff" src="click_off.wav"></audio>\n')
		f.write('    <a-scene background="color: %s;">\n' % color1)
		f.write('      <a-entity id="camera" camera look-controls wasd-controls="acceleration: 5;" position="0.0 1.6 0.0"></a-entity>\n')
		f.write('      <a-entity light="type: ambient;"></a-entity>\n')
		f.write('      <a-entity id="leftController" hand-controls="hand: left; handModelStyle: highPoly; color: #7F7F7F"></a-entity>\n')
		f.write('      <a-entity id="rightController" hand-controls="hand: right; handModelStyle: highPoly; color: #7F7F7F"></a-entity>\n')
		f.write('      <a-entity id="leftHand" hand-tracking-controls="hand: left; modelColor: #7F7F7F;"></a-entity>\n')
		f.write('      <a-entity id="rightHand" hand-tracking-controls="hand: right; modelColor: #7F7F7F"></a-entity>\n')
		if not ar:
			f.write('      <a-circle position="0.0 0.0 0.0" radius="%f" rotation="-90 0 0" color="%s"></a-circle>\n' % (radius, color2))
		f.write('      <a-network position="0.0 0.0 0.0" rotation="0 0 0" node_size="%f" edge_opacity="0.2" src="url(%s.ply)"></a-network>\n' % (nodesize, prefix))
		f.write('    </a-scene>\n')
		f.write('    <script>\n')
		f.write('      const node_names = [%s];\n' % ','.join(names))
		f.write('      const node_positions = [%s];\n' % ','.join(positions))
		f.write('      function toggle_label(index, labels, positions) {\n')
		f.write('        var existing = document.getElementById("label"+index);\n')
		f.write('        if (existing) {\n')
		f.write('          document.getElementById("audioOff").play();\n')
		f.write('          existing.parentElement.removeChild(existing);\n')
		f.write('        }\n')
		f.write('        else {\n')
		f.write('          document.getElementById("audioOn").play();\n')
		f.write('          var entity = document.createElement("a-entity");\n')
		f.write('          entity.setAttribute("id", "label"+index);\n')
		f.write('          entity.setAttribute("look-at", "#camera");\n')
		f.write('          entity.setAttribute("position", {x: positions[index*3], y: positions[index*3+1], z: positions[index*3+2]});\n')
		f.write('          entity.setAttribute("scale", {x: %f, y: %f, z: %f});\n' % (10*nodesize, 10*nodesize, 10*nodesize))
		f.write('          entity.setAttribute("text", {anchor: "left", baseline: "bottom", color: "%s", value: labels[index]});\n' % color3)
		f.write('          document.querySelector("a-scene").appendChild(entity);\n')
		f.write('        }\n')
		f.write('      }\n')
		f.write('      function find_nearest(position, positions) {\n')
		f.write('        var nearest_d = 1000.0;\n')
		f.write('        var nearest_i = null;\n')
		f.write('        for (let i = 0; i < node_positions.length; i += 3) {\n')
		f.write('          let d = Math.sqrt((position.x-positions[i])**2+(position.y-positions[i+1])**2+(position.z-positions[i+2])**2);\n')
		f.write('          if (d < nearest_d) {\n')
		f.write('            nearest_d = d;\n')
		f.write('            nearest_i = i/3;\n')
		f.write('          }\n')
		f.write('        }\n')
		f.write('        if (nearest_d < 0.1) {\n')
		f.write('          toggle_label(nearest_i, node_names, positions);\n')
		f.write('        }\n')
		f.write('      }\n')
		f.write('      document.getElementById("leftController").addEventListener("gripdown", function (event) {\n')
		f.write('        find_nearest(document.getElementById("leftController").getAttribute("position"), node_positions);\n')
		f.write('      });\n')
		f.write('      document.getElementById("rightController").addEventListener("gripdown", function (event) {\n')
		f.write('        find_nearest(document.getElementById("rightController").getAttribute("position"), node_positions);\n')
		f.write('      });\n')
		f.write('      document.getElementById("leftHand").addEventListener("pinchstarted", function (event) {\n')
		f.write('        find_nearest(event.detail.position, node_positions);\n')
		f.write('      });\n')
		f.write('      document.getElementById("rightHand").addEventListener("pinchstarted", function (event) {\n')
		f.write('        find_nearest(event.detail.position, node_positions);\n')
		f.write('      });\n')
		f.write('    </script>\n')
		f.write('  </body>\n')
		f.write('</html>\n');
	finally:
		f.close()

def write_ply(prefix, network, dark):
	f = open(prefix+'.ply', 'w')
	try:
		f.write('ply\nformat ascii 1.0\n')
		f.write('element vertex %d\nproperty float x\nproperty float y\nproperty float z\nproperty uint8 red\nproperty uint8 green\nproperty uint8 blue\n' % len(network['nodes']))
		f.write('element edge %d\nproperty int vertex1\nproperty int vertex2\nproperty uint8 red\nproperty uint8 green\nproperty uint8 blue\n' % len(network['edges']))
		f.write('end_header\n')
		for node in network['nodes']:
			color = '255 255 255'
			if dark:
				color = '255 255 255'
			if 'color' in node:
				h = node['color'].lstrip('#')
				color = ' '.join(tuple(str(int(h[i:i+2], 16)) for i in (0, 2, 4)))
			f.write('%.6f %.6f %.6f %s\n' % (node['x'], node['y'], node['z'], color))
		for edge in network['edges']:
			color = '0 0 0'
			if dark:
				color = '255 255 255'
			if 'color' in edge:
				h = edge['color'].lstrip('#')
				color = ' '.join(tuple(str(int(h[i:i+2], 16)) for i in (0, 2, 4)))
			f.write('%d %d %s\n' % (edge['source'], edge['target'], color))
	finally:
		f.close()

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Convert Cytoscape XGMML file to VR visualization.')
	parser.add_argument('--ar', dest='ar', action='store_true', help='optimize for AR (default is VR).')
	parser.add_argument('--dark', dest='dark', action='store_true', help='use dark background (default is light).')
	parser.add_argument('--depth', dest='depth', default=0.25, type=float, help='depth/thickness of network (default is 0.25)')
	parser.add_argument('--geometry', dest='geometry', default='hemisphere', help='geometry network projection (default is "hemisphere")')
	parser.add_argument('--names', dest='names', default='name', help='column to use for node names (default is "name")')
	parser.add_argument('--nodesize', dest='nodesize', default=0.02, help='size of nodes (default is 0.02)')
	parser.add_argument('--prefix', dest='prefix', default='vr', help='prefix for output files (default is "vr")')
	parser.add_argument('--radius', dest='radius', default=2.2, type=float, help='radius of hemisphere (default is 2.5)')
	parser.add_argument('--scale', dest='scale', default=1.0, type=float, help='scale down network (default is 1.0)')
	parser.add_argument('file')
	args = parser.parse_args()

	network = read_xgmml(args.file, args.names)
	center_network(network)
	create_network_depth(network, args.depth)
	if args.geometry == 'hemisphere':
		scale_network_circle(network, args.scale)
		project_network_hemisphere(network, args.radius)
	elif args.geometry == 'floor':
		scale_network_circle(network, args.scale)
		project_network_floor(network, args.radius)
	elif args.geometry == 'wall':
		scale_network_rectangle(network, math.pi*args.radius)
		project_network_wall(network, args.radius)
	write_html(args.prefix, network, args.ar, args.dark, args.nodesize, args.radius)
	write_ply(args.prefix, network, args.dark)
