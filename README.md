# Cy2VR: Cytoscape to Virtual Reality

## Introduction

This tool allows [Cytoscape](https://cytoscape.org) networks and bring them into Virtual Reality (VR). As the source networks are generally 2D, the tool allows the network to projected in various ways onto 3D shapes, e.g., a hemisphere. The resulting VR version of the network comes in the form of a web page (HTML) and a polygon file (PLY), and it can be viewed in any modern web browser. As it it is based on the WebXR standard, the VR functionality should work on any VR headset.

It has been tested only on the Oculus/Meta Quest 2 headset where the frame rate is acceptable for networks up to around 20k nodes+edges. It has limited interactivity, allowing the user to select nodes to show their names. This can be done either with the controllers by grabbing the node or with hand tracking by pinching the nodes.

Examples of how the result can look:
- [Co-expression network created with FAVA](https://download.jensenlab.org/vr/fava_light.html)
- [STRING network colored with U-CIE](https://download.jensenlab.org/vr/u-cie_dark.html)

## How to use

The codebase is still at the prototype stage. It consists of two main parts, namely a Python script that does the conversion and a custom [A-Frame](https://aframe.io) component coded in JavaScript that shows the network in VR. The workflow is as follows:
1. Create and layout your network in Cytoscape
2. Export the network in XGMML format
3. Use cy2vr.py to produce the HTML and PLY files
4. Copy these, the A-Frame component and sound assets to your web server
5. Open the HTML page in the browser of your VR headset

## Future plans

Create Flask wrapper for the converter and host an instance. This will allow users to simply upload an XGMML file to have it converted and view it without the need to have their own web server to host it on. This could then also be exposed as a RESTful API, allowing for the development of a Cytoscape app that could send the data directly from Cytoscape.
