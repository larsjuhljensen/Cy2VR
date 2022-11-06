(function(modules) { // webpackBootstrap
	var installedModules = {};

	// The require function
	function __webpack_require__(moduleId) {

		// Check if module is in cache
		if(installedModules[moduleId])
			return installedModules[moduleId].exports;

		// Create a new module (and put it into the cache)
		var module = installedModules[moduleId] = {
			exports: {},
			id: moduleId,
			loaded: false
		};

		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
		module.loaded = true;
		return module.exports;
	}

	__webpack_require__.m = modules;
	__webpack_require__.c = installedModules;
	__webpack_require__.p = "";

	return __webpack_require__(0);
})
/************************************************************************/
([
(function(module, exports, __webpack_require__) {

	__webpack_require__(1);

	if (typeof AFRAME === 'undefined') {
		throw new Error('Component attempted to register before AFRAME was available.');
	}

	/**
	 * Point Cloud component for A-Frame.
	 */
	AFRAME.registerComponent('network', {
		schema: {
			src: {
				type: 'asset'
			},
			node_opacity: {
				type: 'number',
				default: 1
			},
			node_size: {
				type: 'number',
				default: 1
			},
			node_texture: {
				type: 'asset'
			},
			edge_opacity: {
				type: 'number',
				default: 1
			},
			edge_width: {
				type: 'number',
				default: 1
			},
			depth_write: {
				type: 'boolean',
				default: true
			},
		},

		multiple: false,

		init: function () {

			if (!this.data.src) {
				console.warn("HOW I'M SUPOSSED TO LOAD A POINT CLOUD WITHOUT [%s] `src` DEFINED", this.name);
				return;
			}

			const loader = new THREE.PLYLoader();
			const _this = this;
			loader.load(this.data.src, function (geometries) {
				var node_material;
				if (_this.data.texture) {
					const sprite = new THREE.TextureLoader().load(_this.data.texture);
					node_material = new THREE.PointsMaterial({
						depth_write: _this.data.depth_write,
						map: sprite,
						opacity: _this.data.node_opacity,
						size: _this.data.node_size,
						transparent: true,
						vertexColors: true
					});
				} else {
					node_material = new THREE.PointsMaterial({
						opacity: _this.data.node_opacity,
						size: _this.data.node_size,
						transparent: true,
						vertexColors: true
					});
				}
				_this.nodes = new THREE.Points(geometries[0], node_material);
				_this.el.setObject3D('nodes', _this.nodes);
				if (geometries.length === 2) {
					var edge_material;
					edge_material = new THREE.LineBasicMaterial({
						linewidth: 1,
						opacity: _this.data.edge_opacity,
						transparent: true,
						vertexColors: true
					});
					_this.edges = new THREE.LineSegments(geometries[1], edge_material);
					_this.el.setObject3D('edges', _this.edges);
				}
			});
		},

		remove: function () {},

	});

	AFRAME.registerPrimitive('a-network', {
	  defaultComponents: {
	    network: {}
	  },
	  mappings: {
		src: 'network.src',
		texture: 'network.texture',
		node_size: 'network.node_size',
		node_opacity: 'network.node_opacity',
		edge_opacity: 'network.edge_opacity',
		depthwrite: 'network.depth_write'
	  }
	});

}),
(function(module, exports) {

	/**
	 * @author Wei Meng / http://about.me/menway
	 *
	 * Description: A THREE loader for PLY ASCII files (known as the Polygon
	 * File Format or the Stanford Triangle Format).
	 *
	 * Limitations: ASCII decoding assumes file is UTF-8.
	 *
	 * Usage:
	 *	var loader = new THREE.PLYLoader();
	 *	loader.load('./models/ply/ascii/dolphins.ply', function (geometry) {
	 *
	 *		scene.add( new THREE.Mesh( geometry ) );
	 *
	 *	} );
	 *
	 * If the PLY file uses non standard property names, they can be mapped while
	 * loading. For example, the following maps the properties
	 * “diffuse_(red|green|blue)” in the file to standard color names.
	 *
	 * loader.setPropertyNameMapping( {
	 *	diffuse_red: 'red',
	 *	diffuse_green: 'green',
	 *	diffuse_blue: 'blue'
	 * } );
	 *
	 */

	THREE.PLYLoader = function (manager) {
		this.manager = (manager !== undefined) ? manager : THREE.DefaultLoadingManager;
		this.propertyNameMapping = {};
	};

	THREE.PLYLoader.prototype = {

		constructor: THREE.PLYLoader,

		load: function ( url, onLoad, onProgress, onError ) {
			var scope = this;
			var loader = new THREE.FileLoader( this.manager );
			loader.setResponseType( 'arraybuffer' );
			loader.load( url, function ( text ) {
				onLoad( scope.parse( text ) );
			}, onProgress, onError );
		},

		setPropertyNameMapping: function ( mapping ) {
			this.propertyNameMapping = mapping;
		},

		parse: function (data) {

			function isASCII(data) {
				var header = parseHeader(bin2str(data));
				return header.format === 'ascii';
			}

			function bin2str(buf) {
				var array_buffer = new Uint8Array(buf);
				var str = '';
				for (var i = 0; i < buf.byteLength; i++) {
					str += String.fromCharCode( array_buffer[i]); // implicitly assumes little-endian
				}
				return str;
			}

			function parseHeader( data ) {

				var patternHeader = /ply([\s\S]*)end_header\s/;
				var headerText = '';
				var headerLength = 0;
				var result = patternHeader.exec( data );

				if ( result !== null ) {
					headerText = result [1];
					headerLength = result[0].length;
				}

				var header = {
					comments: [],
					elements: [],
					headerLength: headerLength
				};

				var lines = headerText.split('\n');
				var currentElement;
				var lineType, lineValues;

				function make_ply_element_property(propertValues, propertyNameMapping) {
					var property = {type: propertValues[0]};
					if ( property.type === 'list' ) {
						property.name = propertValues[3];
						property.countType = propertValues[1];
						property.itemType = propertValues[2];
					} else {
						property.name = propertValues[1];
					}
					if (property.name in propertyNameMapping) {
						property.name = propertyNameMapping[property.name];
					}
					return property;
				}

				for (var i = 0; i < lines.length; i++) {
					var line = lines[ i ];
					line = line.trim();
					if ( line === '' ) continue;
					lineValues = line.split( /\s+/ );
					lineType = lineValues.shift();
					line = lineValues.join( ' ' );
					switch (lineType) {
						case 'format':
							header.format = lineValues[0];
							header.version = lineValues[1];
							break;
						case 'comment':
							header.comments.push(line);
							break;
						case 'element':
							if (currentElement !== undefined) {
								header.elements.push(currentElement);
							}
							currentElement = {};
							currentElement.name = lineValues[0];
							currentElement.count = parseInt(lineValues[1]);
							currentElement.properties = [];
							break;
						case 'property':
							currentElement.properties.push(make_ply_element_property(lineValues, scope.propertyNameMapping));
							break;
						default:
							console.log('unhandled', lineType, lineValues);
					}
				}
				if (currentElement !== undefined) {
					header.elements.push(currentElement);
				}
				return header;
			}

			function parseASCIINumber(n, type) {
				switch (type) {
					case 'char': case 'uchar': case 'short': case 'ushort': case 'int': case 'uint':
					case 'int8': case 'uint8': case 'int16': case 'uint16': case 'int32': case 'uint32':
						return parseInt(n);
					case 'float': case 'double': case 'float32': case 'float64':
						return parseFloat(n);
				}
			}

			function parseASCIIElement(properties, line) {
				var values = line.split(/\s+/);
				var element = {};
				for (var i = 0; i < properties.length; i++) {
					if (properties[i].type === 'list') {
						var list = [];
						var n = parseASCIINumber(values.shift(), properties[i].countType);
						for (var j = 0; j < n; j++) {
							list.push(parseASCIINumber(values.shift(), properties[i].itemType));
						}
						element[properties[i].name] = list;

					} else {
						element[properties[i].name] = parseASCIINumber(values.shift(), properties[i].type);
					}
				}
				return element;
			}

			function parseASCII(data) {

				// PLY ascii format specification, as per http://en.wikipedia.org/wiki/PLY_(file_format)

				var buffer = {
					nodes : [],
					nodecolors : [],
					edges : [],
					edgecolors : []
				};

				var result;
				var header = parseHeader(data);
				var patternBody = /end_header\s([\s\S]*)$/;
				var body = '';
				if ((result = patternBody.exec(data)) !== null) {
					body = result[1];
				}

				var lines = body.split('\n');
				var currentElement = 0;
				var currentElementCount = 0;
				for (var i = 0; i < lines.length; i++) {
					var line = lines[i];
					line = line.trim();
					if (line === '') {
						continue;
					}
					if (currentElementCount >= header.elements[currentElement].count) {
						currentElement++;
						currentElementCount = 0;
					}
					var element = parseASCIIElement(header.elements[currentElement].properties, line);
					handleElement(buffer, header.elements[currentElement].name, element);
					currentElementCount++;
				}
				return postProcess(buffer);
			}

			function postProcess(buffer) {
				var node_geometry = new THREE.BufferGeometry();
				node_geometry.setAttribute('position', new THREE.Float32BufferAttribute(buffer.nodes, 3));
				if (buffer.nodecolors.length > 0) {
					node_geometry.setAttribute('color', new THREE.Float32BufferAttribute(buffer.nodecolors, 3));
				}
				node_geometry.computeBoundingSphere();
				var edge_geometry = new THREE.BufferGeometry();
				edge_geometry.setAttribute('position', new THREE.Float32BufferAttribute(buffer.edges, 3));
				if (buffer.edgecolors.length > 0) {
					edge_geometry.setAttribute('color', new THREE.Float32BufferAttribute(buffer.edgecolors, 3));
				}
				edge_geometry.computeBoundingSphere();
				return [node_geometry, edge_geometry];
			}

			function handleElement( buffer, elementName, element ) {
				if (elementName === 'vertex') {
					buffer.nodes.push(element.x, element.y, element.z);
					if ('red' in element && 'green' in element && 'blue' in element) {
						buffer.nodecolors.push(element.red/255.0, element.green/255.0, element.blue/255.0);
					}
				} else if ( elementName == 'edge' ) {
					buffer.edges.push(
						buffer.nodes[3*element.vertex1], buffer.nodes[3*element.vertex1+1], buffer.nodes[3*element.vertex1+2],
						buffer.nodes[3*element.vertex2], buffer.nodes[3*element.vertex2+1], buffer.nodes[3*element.vertex2+2]
					);
					if ('red' in element && 'green' in element && 'blue' in element) {
						buffer.edgecolors.push(element.red/255.0, element.green/255.0, element.blue/255.0);
						buffer.edgecolors.push(element.red/255.0, element.green/255.0, element.blue/255.0);
					}
				}
			}

			var scope = this;
			if (data instanceof ArrayBuffer) {
				data = bin2str(data);
			}
			return parseASCII(data);
		}

	};

})
]);
