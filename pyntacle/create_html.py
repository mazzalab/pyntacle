import pandas as pd
import numpy as np
import json


string_1file="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Graph from Adjacency Matrix</title>
    <script src="https://d3js.org/d3.v5.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.3.2/html2canvas.min.js"></script>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <!-- Include your custom styles here -->

    <style>


        .search-window {
            padding: 2%;
            border: 1px solid #ccc;
            border-radius: 5px;
            background-color: #fff;
            width: 100%;

            /* Bootstrap classes can handle positioning if needed, like 'fixed-top' */
        }

        .search-window label,
        .search-window input {

        }

        .search-window button {
            background-color: #e0f2f1;
        }

        * {
            margin: 2;
            padding: 20;
            box-sizing: border-box;
        }


        .flex-container {
            display: flex; /* Enables flexbox */
            align-items: center; /* Centers items vertically */
            justify-content: flex-start; /* Centers items horizontally */
        }

        .resized-image {
            width: 100%; /* Adjust as needed */
            height: auto; /* Maintains aspect ratio */
            margin-bottom: 2%; 
            margin-top: 1%; 

        }

        .title-text {
            font-size: 100%; /* Adjust as needed */
        }

        .network-overview {
            border: 1px solid #ccc;
            border-radius: 5px;
            background-color: #fff;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .network-overview-header {
            background-color: #e0f2f1;
            color: #00796b;
            padding: 0.5rem 1rem;
            border-radius: 4px 4px 0 0;
            margin: -1rem -1rem 1rem -1rem;
            font-weight: bold;
        }

        .svg-outer-box {
            display: flex;
            justify-content: center; /* Centers the content horizontally */
            align-items: center;
            background-color: #e0f2f1; /* Same as network overview header */
            padding: 1%;
            border-radius: 10px;
            border: 1px solid #ccc;
            margin-bottom: 1%;
        }

        .Network-container {
            display: flex;
            justify-content: center; /* Centers the content horizontally */
            align-items: center; /* Centers the content vertically */
            width: 100%; /* Adjust as needed */
            height: auto;
        }


        
        svg {
            border: 1px solid #ccc; /* Example: Black border, 2px width */
            border-radius: 10px; /* Optional: if you want rounded corners */
            background-color: #ffff; /* Same as network overview header */

        }

        .links line {
            stroke: #999;
            stroke-opacity: 0.6;
        }

        .nodes circle {
            stroke: #fff;
            stroke-width: 1.5px;
        }

        .nodetext {
            visibility: hidden;
            font-size: 12px;
            font-family: Arial, sans-serif;
        }

        .hovered-node {
            fill: #ffce44; /* Change fill color to yellow */
        }

        .clicked-node {
            fill: #ffce44 !important; /* Change fill color for clicked nodes */
        }

        .neighbor-node {
            fill: #de5246; /* Change fill color for neighbor nodes */
        }

        .highlighted-link {
            stroke: #de5246 !important; /* Change stroke color to blue for highlighted links */
            stroke-opacity: 0.2 !important;
            stroke-width: 2; 
        }


        .label-toggle-text {
            margin-right: 1px; /* Distanza tra la scritta e il toggle */
            margin-left: 20px;
            margin-top: 7px;
            display: inline-block; /* Permette che la scritta e il toggle siano sulla stessa riga */
            vertical-align: middle; /* Allinea verticalmente al centro */
        }


        .switch {
            position: relative;
            display: inline-block;
            width: 30px;
            height: 17px;
            top: 5px;

        }

        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            -webkit-transition: .4s;
            transition: .4s;

        }

        .slider:before {
            position: absolute;
            content: "";
            height: 13px;
            width: 13px;
            left: 2px;
            bottom: 2px;
            background-color: white;
            -webkit-transition: .4s;
            transition: .4s;

        }

        input:checked + .slider {
            background-color: #32cd32;
        }

        input:focus + .slider {
            box-shadow: 0 0 1px #32cd32;
        }

        input:checked + .slider:before {
            -webkit-transform: translateX(13px);
            -ms-transform: translateX(13px);
            transform: translateX(13px);
        }

        /* Rounded sliders */
        .slider.round {
            border-radius: 34px;
        }

        .slider.round:before {
            border-radius: 50%;
        }


    </style>


</head>
<body>

    <!-- Use Bootstrap's container for responsive layout -->
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-4">
                <img src="https://camo.githubusercontent.com/21117091dc0315536e4ad1ccf7548c87c4626bc3563c1c96e3b40430114a3ae5/687474703a2f2f70796e7461636c652e6373732d6d656e64656c2e69742f696d616765732f7469746c655f6a6f696e65642e706e67" class="resized-image">
            </div>
        <div>

            </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <div class="row">
                        <div class="col-md-12">
                            <div class="title-text">"""



string_2file="""</div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-9">

                            <div class="svg-outer-box">
                                <div class="Network-container" id="box-to-export">
                                    <svg viewBox="0 0 1200 600" preserveAspectRatio="xMidYMid meet"></svg>
                                </div>
                            </div>
                            <button id="export-box-svg" class="btn btn-primary" >Export as SVG</button>
                            <label for="label-toggle" class="label-toggle-text">Show Node Labels:</label>
                            <label class="switch">
                                <input type="checkbox" id="label-toggle">
                                <span class="slider round"></span>
                            </label>
                        </div>
                        <div class="col-md-3">
                                <div class="search-window">
                                    <!-- Network Overview section -->
                                    <div class="network-overview">
                                        <div class="network-overview-header">                                        
                                            <h2>Network Overview</h2>
                                        </div>

                                        <ul>
                                            <li>"""


string_4file="""
        
        var nodes="""




string_7file="""';

            // Attiva il download
            document.body.appendChild(downloadLink);
            downloadLink.click();

            // Pulizia
            document.body.removeChild(downloadLink);
            cloneSvg.remove();
        }

        document.getElementById('export-box-svg').addEventListener('click', downloadSVG);




        document.getElementById('label-toggle').addEventListener('change', function() {
            if(this.checked) {
                d3.selectAll('.nodetext text').style('visibility', 'visible');
            } else {
                d3.selectAll('.nodetext text').style('visibility', 'hidden');
            }
        });




    </script>
</body>
</html>
"""

















#########################################################################################################################################################################################
#########################################################################################################################################################################################
#########################################################################################################################################################################################



def create_local_html(df_metrics,grafo,outdir):

	adj_matrix = grafo.get_adjacency()
	str_matrix = str(adj_matrix)

	# Rimuovere spazi iniziali e finali e suddividere la stringa in righe
	str_matrix = str_matrix.strip().split('\n')
	# Unire le righe in una singola stringa, rimuovendo spazi inutili
	str_matrix = ', '.join(line.strip() for line in str_matrix)

	str_names=str(grafo.vs["name"])

	df_string=json.dumps([{"Node Name": node} | row.to_dict() for node, row in df_metrics.iterrows()])

	info_net="Removed nodes: "+str({grafo.removed})+"""</li>
                                            <li>Number of components: """+str(len(grafo.components()))+"""</li>
                                            <li>Number of Nodes: """+str(len(grafo.vs['label']))+"""</li>
                                            <li>Number of Edges: """+str(len(grafo.get_edgelist()))+"""</li>
                                        """


	name_output=str(grafo.name)+str(".svg")



	
	string_3file="""</ul>
                                    </div>

                                    <div class="row">
                                        <div class="col-12">
                                            <label for="node-search">Search Node:</label>
                                            <input type="text" id="node-search" placeholder="Enter node name">
                                            <button onclick="searchNode()">Search</button>
                                        </div>
                                    </div>
                                    <div class="row mt-3">
                                        <div class="col-12">
                                    <!-- Dropdown menu for selecting metrics -->
                                    <label for="metric-select">Select Metric:</label>
                                    <select id="metric-select">
                                        <option value="Degree">Degree</option>
                                        <option value="Betweenness">Betweenness</option>
                                        <option value="Closeness">Closeness</option>
                                        <option value="Radiality">Radiality</option>
                                        <option value="Radiality reach">Radiality reach</option>
                                        <option value="Clustering Coefficient">Clustering Coefficient</option>
                                        <option value="Eccentricity">Eccentricity</option>
                                        <option value="Eigenvector (Scaled)">Eigenvector (Scaled)</option>
                                        <option value="Pagerank">Pagerank</option>
                                    </select>
                                    <!-- Slider for metric values -->
                                    <input type="range" id="metric-slider" min="0" max="1" step="0.01">
                                        </div>
                                    </div>
                                    <div id="slider-value">Value: 0</div>
                                    <div id="slider-range">Range: 0 to 1</div>
                                    
                                    <h4>Node Information</h4>
                                    <div class="col-md-12">
                                        <div id="tooltip">
                                            <div id="node-details">Click on a node to see its details here...</div>
                                        </div>
                                    </div>
                                </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>


    <!-- Optional: include Bootstrap JS and its dependencies -->
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.16.0/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>

    <!-- Your custom scripts -->
    <script>
        // Global variable to keep track of the first selected node
        var firstSelectedNode = null;

        var highlightedNode = null;

        var svg = d3.select("svg"),
            width = +svg.attr("width"),
            height = +svg.attr("height");

        var g = svg.append("g");

        var zoom = d3.zoom()
            .scaleExtent([0.5, 10])
            .on("zoom", zoomed);

        svg.call(zoom);

        function zoomed() {
            g.attr("transform", d3.event.transform);
        }


        var initialValue = document.getElementById('metric-slider').value;
        document.getElementById('slider-value').textContent = `Value: ${initialValue}`;



        // Function to clear all highlights
        function clearHighlights() {
            d3.selectAll('.nodes circle').classed('clicked-node', false);
            d3.selectAll('.nodes circle').classed('neighbor-node', false);
            d3.selectAll('.links line').classed('highlighted-link', false);
            d3.select("#tooltip").style("display", "none");
            highlightedNode = null;

        }

        var matrix ="""


	string_5file=""".map(function(id, index) {
            return { id: id, group: index };
        });

        // Information table
        var nodeInfo = """



	string_6file=""";
        var links = [];
        matrix.forEach(function(row, i) {
            row.forEach(function(cell, j) {
                if (cell === 1) {
                    links.push({ source: nodes[i].id, target: nodes[j].id });
                }
            });
        });

        var simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(function(d) { return d.id; }))
            .force("charge", d3.forceManyBody())
            .force("center", d3.forceCenter(1200 / 2, 600 / 2)); // Coordinates based on the viewBox

        var link = g.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(links)
            .enter()
            .append("line")
            .attr("id", function(d) { return "link-" + d.source.id + "-" + d.target.id; })

        var node = g.append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(nodes)
            .enter()
            .append("circle")
            .attr("r", 5)
            .attr("id", function(d) { return "node-" + d.id; })
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended))
                .on("click", showNodeInfo);

        var labels = g.append("g")
            .attr("class", "nodetext")
            .selectAll("text")
            .data(nodes)
            .enter()
            .append("text")
            .text(function(d) { return d.id; })
            .style("visibility", "hidden");

        node.on("mouseover", function(d) {
            d3.select(this).classed('hovered-node', true);
            labels
                .filter(function(node) { return node.id === d.id; })
                .style("visibility", "visible");
        });

        node.on("mouseout", function(d) {
            if (highlightedNode && d.id === highlightedNode.id) {
                return; // Do not remove the highlight if this is the currently selected node
            }

            
            d3.select(this).classed('hovered-node', false);
            labels
                .filter(function(node) { return node.id === d.id; })
                .style("visibility", "hidden");
        });

        simulation
            .nodes(nodes)
            .on("tick", ticked)
            .on("end", function() {
            });

        simulation.force("link")
            .links(links);

        function ticked() {
            link
                .attr("x1", function(d) { return d.source.x; })
                .attr("y1", function(d) { return d.source.y; })
                .attr("x2", function(d) { return d.target.x; })
                .attr("y2", function(d) { return d.target.y; });

            node
                .attr("cx", function(d) { return d.x; })
                .attr("cy", function(d) { return d.y; });

            labels
                .attr("x", function(d) { return d.x + 8; })
                .attr("y", function(d) { return d.y + 3; });
        }



        function dragstarted(d) {
            if (!d3.event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(d) {
            d.fx = d3.event.x;
            d.fy = d3.event.y;
        }

        function dragended(d) {
            if (!d3.event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        svg.on("click", function() {
            d3.select("#tooltip").style("display", "none");            
            clearHighlights()
        });



        function searchNode() {
            var searchTerm = document.getElementById('node-search').value.toUpperCase();

            // Reset previous highlights
            clearHighlights();

            // Find and highlight the searched node
            var searchedNode = nodes.find(function (node) {
                return node.id.toUpperCase() === searchTerm;
            });

            if (searchedNode) {
                d3.select('#node-' + searchedNode.id)
                    .classed('clicked-node', true);
            }
        }
        document.getElementById('node-search').addEventListener('keypress', function(event) {
            if (event.keyCode === 13) {
                searchNode();
            }
        });

        // Update slider range based on selected metric
        document.getElementById('metric-select').addEventListener('change', function() {
            var selectedMetric = this.value;
            updateSliderRange(selectedMetric);
        });



        function updateSliderRange(metric) {
            var metricValues = nodeInfo.map(node => node[metric]);
            var minVal = Math.min(...metricValues);
            var maxVal = Math.max(...metricValues);
            var slider = document.getElementById('metric-slider');
            slider.min = minVal;
            slider.max = maxVal;
            slider.value = minVal; // Reset slider to minimum value

            // Update slider range display
            document.getElementById('slider-range').textContent = `Range: ${minVal} to ${maxVal}`;
        }




        document.getElementById('metric-slider').addEventListener('input', function() {
            var sliderValue = +this.value;

            // Update the slider value display
            document.getElementById('slider-value').textContent = `Value: ${sliderValue}`;

            var selectedMetric = document.getElementById('metric-select').value;
            filterNodes(selectedMetric, sliderValue);
        });

        function filterNodes(metric, value) {
            node.style('display', function(d) {
                var display = nodeInfo.find(n => n["Node Name"] === d.id)[metric] >= value ? 'inline' : 'none';
                // Aggiorna la visibilità dei labels in base ai nodi
                labels.filter(function(l) { return l.id === d.id; })
                    .style('visibility', display === 'inline' ? 'visible' : 'hidden');
                return display;
            });
            link.style('display', function(d) {
                return nodeInfo.find(n => n["Node Name"] === d.source.id)[metric] >= value && 
                       nodeInfo.find(n => n["Node Name"] === d.target.id)[metric] >= value ? 'inline' : 'none';
            });
        }

        // Initial setup for slider
        updateSliderRange('Degree'); // Default metric

        function showNodeInfo(d) {
            d3.event.stopPropagation(); // Stop event from propagating to the SVG
            // Reset all nodes and links to their original styles
            d3.selectAll('.nodes circle').classed('clicked-node', false).classed('neighbor-node', false);
            d3.selectAll('.links line').classed('highlighted-link', false); // Add this line

            // Highlight the clicked node
            d3.select(this).classed('clicked-node', true);
            
            // Highlight all neighboring nodes and the links connecting them
            links.forEach(function(link) {
                if (link.source.id === d.id || link.target.id === d.id) {
                    var neighborNode = d3.selectAll('.nodes circle')
                        .filter(function(n) { return n.id === link.source.id || n.id === link.target.id; });
                    
                    neighborNode.classed('neighbor-node', true);

                    d3.select("#link-" + link.source.id + "-" + link.target.id).classed('highlighted-link', true);
                }

            });


            if (highlightedNode) {
                highlightedNode.classed('hovered-node', false);
            }

            // Highlight the clicked node and update the highlightedNode variable
            var currentNode = d3.select(this).classed('hovered-node', true);
            highlightedNode = currentNode;

            var info = nodeInfo.find(function(node) { return node["Node Name"] === d.id; });

            if (info) {
                console.log(info)
                var tooltip = d3.select("#tooltip");
                tooltip.html("<strong>Node Name:</strong> " + info["Node Name"] + "<br>" +
                             "<strong>Degree:</strong> " + info["Degree"] + "<br>" +
                             "<strong>Betweenness:</strong> " + info["Betweenness"] + "<br>" +
                             "<strong>Closeness:</strong> " + info["Closeness"] + "<br>" +
                             "<strong>Radiality:</strong> " + info["Radiality"] + "<br>" +
                             "<strong>Radiality reach:</strong> " + info["Radiality reach"] + "<br>" +
                             "<strong>Clustering Coefficient:</strong> " + info["Clustering Coefficient"] + "<br>" +
                             "<strong>Eccentricity:</strong> " + info["Eccentricity"] + "<br>" +
                             "<strong>Eigenvector (Scaled):</strong> " + info["Eigenvector (Scaled)"] + "<br>" +
                             "<strong>Pagerank:</strong> " + info["Pagerank"]);
                tooltip.style("left", (d3.event.pageX) + "px")
                       .style("top", (d3.event.pageY) + "px")
                       .style("display", "block");
            }
        }



        function downloadSVG() {
            // Crea un nuovo elemento SVG
            var cloneSvg = d3.select('body').append('svg');


            cloneSvg.selectAll('.links')
                .data(link.data())
                .enter()
                .append('line')
                .attr('x1', function(d) { return d.source.x; })
                .attr('y1', function(d) { return d.source.y; })
                .attr('x2', function(d) { return d.target.x; })
                .attr('y2', function(d) { return d.target.y; })
                .attr('stroke', function(d) {
                    // Applica lo stile della classe highlighted-link se presente
                    if (d3.select("#link-" + d.source.id + "-" + d.target.id).classed('highlighted-link')) {
                        return "#de5246"; // Colore specificato nella classe highlighted-link
                    } else {
                        return d3.select("#link-" + d.source.id + "-" + d.target.id).style("stroke");
                    }
                })
                .attr('stroke-opacity', 0.2)
                .attr('stroke-width', 2);

            // Clona e appendi i nodi
            cloneSvg.selectAll('.nodes')
                .data(node.data())
                .enter()
                .append('circle')
                .attr('r', 5)
                .attr('cx', function(d) { return d.x; })
                .attr('cy', function(d) { return d.y; })
                .attr('fill', function(d) { 
                    var originalNode = d3.select("#node-" + d.id);
                    var fillColor = originalNode.style("fill"); // Colore di default

                    // Applica il colore giallo se il nodo è cliccato
                    if (originalNode.classed('clicked-node')) {
                        fillColor = "#ffce44"; // Colore giallo specifico
                    }
                    
                    // Altri controlli possono essere inseriti qui se necessario

                    return fillColor;
                });


            // Controlla se il toggle per le etichette è attivo
            if (document.getElementById('label-toggle').checked) {
                // Clona e appendi le etichette dei nodi
                cloneSvg.selectAll('.nodetext')
                    .data(labels.data())
                    .enter()
                    .append('text')
                    .text(function(d) { return d.id; })
                    .attr('x', function(d) { return d.x + 8; })
                    .attr('y', function(d) { return d.y + 3; })
                    .attr('visibility', 'visible');
            }





            // Calcola il bounding box del grafico
            var bbox = g.node().getBBox();

            // Definisci il margine desiderato
            var margin = 300; // Ad esempio, 50px di margine

            // Calcola le nuove dimensioni con il margine
            var newWidth = bbox.width + margin;
            var newHeight = bbox.height + margin;

            // Aggiusta il viewBox per centrare il grafico con un margine extra
            cloneSvg.attr('viewBox', `${bbox.x - margin / 2} ${bbox.y - margin / 2} ${newWidth} ${newHeight}`)

            
            // Serializza il nuovo SVG
            var serializer = new XMLSerializer();
            var source = serializer.serializeToString(cloneSvg.node());

            // Crea un Blob dal sorgente
            var svgBlob = new Blob([source], {type: 'image/svg+xml;charset=utf-8'});
            var downloadLink = document.createElement('a');
            downloadLink.href = URL.createObjectURL(svgBlob);
            downloadLink.download = '"""

	final_string=string_1file+str(grafo.name)+string_2file+info_net+string_3file+str_matrix+";"+string_4file+str_names+string_5file+df_string+string_6file+name_output+string_7file

	with open(outdir+"/"+grafo.name+"_local.html", 'w') as f:
	    f.write(final_string)




































#######################################################################################################################################################################
#######################################################################################################################################################################
#######################################################################################################################################################################
#######################################################################################################################################################################


def create_keyplayer_html(df_metrics,grafo,outdir,filename):


	adj_matrix = grafo.get_adjacency()
	str_matrix = str(adj_matrix)
	str_matrix = str_matrix.strip().split('\n')
	str_matrix = ', '.join(line.strip() for line in str_matrix)

	str_names=str(grafo.vs["name"])
	
	df_string=json.dumps([row.to_dict() for node, row in df_metrics.iterrows()])

	info_net="Removed nodes: "+str({grafo.removed})+"""</li>
                                            <li>Number of components: """+str(len(grafo.components()))+"""</li>
                                            <li>Number of Nodes: """+str(len(grafo.vs['label']))+"""</li>
                                            <li>Number of Edges: """+str(len(grafo.get_edgelist()))+"""</li>
            """
    

	name_output=str(filename)+str(".svg")


	string_3file="""</ul>
                                </div>

                                <div class="row">
                                    <div class="col-12">
                                        <label for="node-search">Search Node:</label>
                                        <input type="text" id="node-search" placeholder="Enter node name">
                                        <button onclick="searchNode()">Search</button>
                                    </div>
                                </div>
                                <div class="row mt-3">
                                    <div class="col-12">
                                <!-- Dropdown menu for selecting metrics -->
                                <label for="metric-select">Select Metric:</label>
                                <select id="metric-select">
                                    <option value="" disabled selected>Select your option</option>
                                    <option value="Clear">Clear</option>
                                    <option value="F">F</option>
                                    <option value="dF">dF</option>
                                    <option value="dR">dR</option>
                                    <option value="mreach">mreach</option>
                                </select>
                                <span id="score-display" style="margin-left: 10px;">Score: --</span>

                                <div>
                                    <label for="set-select">Select Node Set:</label>
                                    <select id="set-select">
                                        <!-- Options will be dynamically added here based on the selected metric -->
                                    </select>
                                </div>
                            </div>
                    </div>
                </div>
            </div>
        </div>
    </div>


    <!-- Optional: include Bootstrap JS and its dependencies -->
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.16.0/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>

    <!-- Your custom scripts -->
    <script>
        // Global variable to keep track of the first selected node
        var firstSelectedNode = null;

        var highlightedNode = null;

        var svg = d3.select("svg"),
            width = +svg.attr("width"),
            height = +svg.attr("height");

        var g = svg.append("g");

        var zoom = d3.zoom()
            .scaleExtent([0.5, 10])
            .on("zoom", zoomed);

        svg.call(zoom);

        function zoomed() {
            g.attr("transform", d3.event.transform);
        }


        // Function to clear all highlights
        function clearHighlights() {
            d3.selectAll('.nodes circle').classed('clicked-node', false);
            d3.selectAll('.nodes circle').classed('neighbor-node', false);
            d3.selectAll('.links line').classed('highlighted-link', false);
            d3.select("#tooltip").style("display", "none");
            highlightedNode = null;

        }

        var matrix =""" 

	string_5file=""".map(function(id, index) {
	            return { id: id, group: index };
	        });

	        function showNodeInfo(d) {
	                    d3.event.stopPropagation(); // Stop event from propagating to the SVG
	                    // Reset all nodes and links to their original styles
	                    d3.selectAll('.nodes circle').classed('clicked-node', false).classed('neighbor-node', false);
	                    d3.selectAll('.links line').classed('highlighted-link', false); // Add this line

	                    // Highlight the clicked node
	                    d3.select(this).classed('clicked-node', true);
	                    
	                    // Highlight all neighboring nodes and the links connecting them
	                    links.forEach(function(link) {
	                        if (link.source.id === d.id || link.target.id === d.id) {
	                            var neighborNode = d3.selectAll('.nodes circle')
	                                .filter(function(n) { return n.id === link.source.id || n.id === link.target.id; });
	                            
	                            neighborNode.classed('neighbor-node', true);

	                            d3.select("#link-" + link.source.id + "-" + link.target.id).classed('highlighted-link', true);
	                        }

	                    });

	                    if (highlightedNode) {
	                        highlightedNode.classed('hovered-node', false);
	                    }

	                    // Highlight the clicked node and update the highlightedNode variable
	                    var currentNode = d3.select(this).classed('hovered-node', true);
	                    highlightedNode = currentNode;

	                }

	        var keyInfo = """

	string_6file=""";
	        var links = [];
	        matrix.forEach(function(row, i) {
	            row.forEach(function(cell, j) {
	                if (cell === 1) {
	                    links.push({ source: nodes[i].id, target: nodes[j].id });
	                }
	            });
	        });

	        var simulation = d3.forceSimulation(nodes)
	            .force("link", d3.forceLink(links).id(function(d) { return d.id; }))
	            .force("charge", d3.forceManyBody())
	            .force("center", d3.forceCenter(1200 / 2, 600 / 2)); // Coordinates based on the viewB


	        var link = g.append("g")
	            .attr("class", "links")
	            .selectAll("line")
	            .data(links)
	            .enter()
	            .append("line")
	            .attr("id", function(d) { return "link-" + d.source.id + "-" + d.target.id; })

	        var node = g.append("g")
	            .attr("class", "nodes")
	            .selectAll("circle")
	            .data(nodes)
	            .enter()
	            .append("circle")
	            .attr("r", 5)
	            .attr("id", function(d) { return "node-" + d.id; })
	            .call(d3.drag()
	                .on("start", dragstarted)
	                .on("drag", dragged)
	                .on("end", dragended))
	                .on("click", showNodeInfo);

	        var labels = g.append("g")
	            .attr("class", "nodetext")
	            .selectAll("text")
	            .data(nodes)
	            .enter()
	            .append("text")
	            .text(function(d) { return d.id; })
	            .style("visibility", "hidden");


	        filterNodes('Clear');

	        node.on("mouseover", function(d) {
	            d3.select(this).classed('hovered-node', true);
	            labels
	                .filter(function(node) { return node.id === d.id; })
	                .style("visibility", "visible");
	        });

	        node.on("mouseout", function(d) {
	            if (highlightedNode && d.id === highlightedNode.id) {
	                return; // Do not remove the highlight if this is the currently selected node
	            }

	            
	            d3.select(this).classed('hovered-node', false);
	            labels
	                .filter(function(node) { return node.id === d.id; })
	                .style("visibility", "hidden");
	        });

	        simulation
	            .nodes(nodes)
	            .on("tick", ticked)
	            .on("end", function() {
	            });

	        simulation.force("link")
	            .links(links);

	        function ticked() {
	            link
	                .attr("x1", function(d) { return d.source.x; })
	                .attr("y1", function(d) { return d.source.y; })
	                .attr("x2", function(d) { return d.target.x; })
	                .attr("y2", function(d) { return d.target.y; });

	            node
	                .attr("cx", function(d) { return d.x; })
	                .attr("cy", function(d) { return d.y; });

	            labels
	                .attr("x", function(d) { return d.x + 8; })
	                .attr("y", function(d) { return d.y + 3; });
	        }



	        function dragstarted(d) {
	            if (!d3.event.active) simulation.alphaTarget(0.3).restart();
	            d.fx = d.x;
	            d.fy = d.y;
	        }

	        function dragged(d) {
	            d.fx = d3.event.x;
	            d.fy = d3.event.y;
	        }

	        function dragended(d) {
	            if (!d3.event.active) simulation.alphaTarget(0);
	            d.fx = null;
	            d.fy = null;
	        }

	        svg.on("click", function() {
	            d3.select("#tooltip").style("display", "none");            
	            clearHighlights()
	        });



            function searchNode() {
                var searchTerm = document.getElementById('node-search').value.toUpperCase();

                // Reset previous highlights
                clearHighlights();

                // Find and highlight the searched node
                var searchedNode = nodes.find(function (node) {
                    return node.id.toUpperCase() === searchTerm;
                });

                if (searchedNode) {
                    var escapedId = searchedNode.id.replace(/\./g, '\\\\.');
                    d3.select('#node-' + escapedId)
                        .classed('clicked-node', true);
                }
            }

            function filterNodes(metric) {
                // Reset all node colors first
                d3.selectAll('.nodes circle').style('fill', 'black'); // default color

                // Find the key pairs for the selected metric
                keyInfo.forEach(function(ki) {
                    if (ki.Operation === metric) {
                        ki["K-set"].forEach(function(pair) {
                            pair.forEach(function(nodeId) {
                                var escapedId = nodeId.replace(/\./g, '\\\\.');
                                d3.select('#node-' + escapedId).style('fill', '#f44336'); // color for selected nodes
                            });
                        });
                    }
                });
            }


	        // Update the event listener for the metric select dropdown
	        document.getElementById('metric-select').addEventListener('change', function() {
	            filterNodes(this.value);
                updateScoreDisplay(this.value);

	        });

            function updateScoreDisplay(metric) {
                var scoreDisplay = document.getElementById('score-display');
                var score = keyInfo.find(ki => ki.Operation === metric)?.Score || '--';
                scoreDisplay.textContent = 'Score: ' + score;
            }


	        document.getElementById('metric-select').addEventListener('change', function() {
	            populateSetDropdown(this.value);
	        });

            function highlightNodes(metric, setIndex) {
                // Reset all node colors first
                d3.selectAll('.nodes circle').style('fill', 'black'); // default color

                var selectedSet = keyInfo.find(ki => ki.Operation === metric)["K-set"][setIndex];
                selectedSet.forEach(function(nodeId) {
                    d3.select('#node-' + nodeId.replace('.', '\\\\.')).style('fill', '#f44336'); 
                });
            }
            




            document.getElementById('set-select').addEventListener('change', function() {
                var metric = document.getElementById('metric-select').value;
                highlightNodes(metric, parseInt(this.value));
            });


            document.getElementById('node-search').addEventListener('keypress', function(event) {
                if (event.keyCode === 13) {
                    searchNode();
                }
            });





            
            
            function populateSetDropdown(metric) {
                var setSelect = document.getElementById('set-select');
                setSelect.innerHTML = ''; // Clear existing options

                var option = document.createElement("option");
                option.value = "";
                option.text = "Select the kp-set";
                option.disabled = true; // Disable this option
                option.selected = true; // Set as the default selected option
                setSelect.appendChild(option);

                keyInfo.forEach(function(ki) {
                    if (ki.Operation === metric) {
                        ki["K-set"].forEach(function(pair, index) {
                            var option = document.createElement("option");
                            option.value = index;
                            option.text = pair.map(node => encodeURIComponent(node)).join(", ");
                            setSelect.appendChild(option);
                        });
                    }
                });
            }




	        function downloadSVG() {
	            // Create a new SVG element
	            var cloneSvg = d3.select('body').append('svg')


	            cloneSvg.selectAll('.links')
	                .data(link.data())
	                .enter()
	                .append('line')
	                .attr('x1', function(d) { return d.source.x; })
	                .attr('y1', function(d) { return d.source.y; })
	                .attr('x2', function(d) { return d.target.x; })
	                .attr('y2', function(d) { return d.target.y; })
	                .attr('stroke', function(d) {
	                    // Applica lo stile della classe highlighted-link se presente
	                    if (d3.select("#link-" + d.source.id + "-" + d.target.id).classed('highlighted-link')) {
	                        return "#de5246"; // Colore specificato nella classe highlighted-link
	                    } else {
	                        return d3.select("#link-" + d.source.id + "-" + d.target.id).style("stroke");
	                    }
	                })
	                .attr('stroke-opacity', 0.2)
	                .attr('stroke-width', 2);

	            // Clona e appendi i nodi
	            cloneSvg.selectAll('.nodes')
	                .data(node.data())
	                .enter()
	                .append('circle')
	                .attr('r', 5)
	                .attr('cx', function(d) { return d.x; })
	                .attr('cy', function(d) { return d.y; })
	                .attr('fill', function(d) { 
	                    var originalNode = d3.select("#node-" + d.id);
	                    var fillColor = originalNode.style("fill"); // Colore di default

	                    // Applica il colore giallo se il nodo è cliccato
	                    if (originalNode.classed('clicked-node')) {
	                        fillColor = "#ffce44"; // Colore giallo specifico
	                    }
	                    
	                    // Altri controlli possono essere inseriti qui se necessario

	                    return fillColor;
	                });




	            // Controlla se il toggle per le etichette è attivo
	            if (document.getElementById('label-toggle').checked) {
	                // Clona e appendi le etichette dei nodi
	                cloneSvg.selectAll('.nodetext')
	                    .data(labels.data())
	                    .enter()
	                    .append('text')
	                    .text(function(d) { return d.id; })
	                    .attr('x', function(d) { return d.x + 8; })
	                    .attr('y', function(d) { return d.y + 3; })
	                    .attr('visibility', 'visible');
	            }

	            // Calcola il bounding box del grafico
	            var bbox = g.node().getBBox();

	            // Definisci il margine desiderato
	            var margin = 300; // Ad esempio, 50px di margine

	            // Calcola le nuove dimensioni con il margine
	            var newWidth = bbox.width + margin;
	            var newHeight = bbox.height + margin;

	            // Aggiusta il viewBox per centrare il grafico con un margine extra
	            cloneSvg.attr('viewBox', `${bbox.x - margin / 2} ${bbox.y - margin / 2} ${newWidth} ${newHeight}`)


	            // Serialize the new SVG
	            var serializer = new XMLSerializer();
	            var source = serializer.serializeToString(cloneSvg.node());

	            // Create a Blob from the source
	            var svgBlob = new Blob([source], {type: 'image/svg+xml;charset=utf-8'});
	            var downloadLink = document.createElement('a');
	            downloadLink.href = URL.createObjectURL(svgBlob);
	            downloadLink.download = '"""


	final_string=string_1file+str(filename)+string_2file+info_net+string_3file+str_matrix+";"+string_4file+str_names+string_5file+df_string+string_6file+name_output+string_7file

	with open(outdir+"/"+filename+"_keyplayer.html", 'w') as f:
	    f.write(final_string)





































#######################################################################################################################################################################
#######################################################################################################################################################################
#######################################################################################################################################################################
#######################################################################################################################################################################


def create_groupcentrality_html(df_metrics,grafo,outdir,filename):


    adj_matrix = grafo.get_adjacency()
    str_matrix = str(adj_matrix)
    str_matrix = str_matrix.strip().split('\n')
    str_matrix = ', '.join(line.strip() for line in str_matrix)

    str_names=str(grafo.vs["name"])
    
    df_string=json.dumps([row.to_dict() for node, row in df_metrics.iterrows()])

    info_net="Removed nodes: "+str({grafo.removed})+"""</li>
                                            <li>Number of components: """+str(len(grafo.components()))+"""</li>
                                            <li>Number of Nodes: """+str(len(grafo.vs['label']))+"""</li>
                                            <li>Number of Edges: """+str(len(grafo.get_edgelist()))+"""</li>
            """
    

    name_output=str(filename)+str(".svg")


    string_3file="""</ul>
                                </div>

                                <div class="row">
                                    <div class="col-12">
                                        <label for="node-search">Search Node:</label>
                                        <input type="text" id="node-search" placeholder="Enter node name">
                                        <button onclick="searchNode()">Search</button>
                                    </div>
                                </div>
                                <div class="row mt-3">
                                    <div class="col-12">
                                <!-- Dropdown menu for selecting metrics -->
                                <label for="metric-select">Select Metric:</label>
                                <select id="metric-select">
                                    <option value="" disabled selected>Select your option</option>
                                    <option value="Clear">Clear</option>
                                    <option value="Degree">Group Degree</option>
                                    <option value="Betweenness">Group Betweenness</option>
                                    <option value="Closeness">Group Closeness</option>
                                </select>
                                <span id="score-display" style="margin-left: 10px;">Score: --</span>

                                <div>
                                    <label for="set-select">Select Node Set:</label>
                                    <select id="set-select">
                                        <!-- Options will be dynamically added here based on the selected metric -->
                                    </select>
                                </div>
                            </div>
                    </div>
                </div>
            </div>
        </div>
    </div>


    <!-- Optional: include Bootstrap JS and its dependencies -->
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.16.0/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>

    <!-- Your custom scripts -->
    <script>
        // Global variable to keep track of the first selected node
        var firstSelectedNode = null;

        var highlightedNode = null;

        var svg = d3.select("svg"),
            width = +svg.attr("width"),
            height = +svg.attr("height");

        var g = svg.append("g");

        var zoom = d3.zoom()
            .scaleExtent([0.5, 10])
            .on("zoom", zoomed);

        svg.call(zoom);

        function zoomed() {
            g.attr("transform", d3.event.transform);
        }


        // Function to clear all highlights
        function clearHighlights() {
            d3.selectAll('.nodes circle').classed('clicked-node', false);
            d3.selectAll('.nodes circle').classed('neighbor-node', false);
            d3.selectAll('.links line').classed('highlighted-link', false);
            d3.select("#tooltip").style("display", "none");
            highlightedNode = null;

        }

        var matrix =""" 

    string_5file=""".map(function(id, index) {
                return { id: id, group: index };
            });

            function showNodeInfo(d) {
                        d3.event.stopPropagation(); // Stop event from propagating to the SVG
                        // Reset all nodes and links to their original styles
                        d3.selectAll('.nodes circle').classed('clicked-node', false).classed('neighbor-node', false);
                        d3.selectAll('.links line').classed('highlighted-link', false); // Add this line

                        // Highlight the clicked node
                        d3.select(this).classed('clicked-node', true);
                        
                        // Highlight all neighboring nodes and the links connecting them
                        links.forEach(function(link) {
                            if (link.source.id === d.id || link.target.id === d.id) {
                                var neighborNode = d3.selectAll('.nodes circle')
                                    .filter(function(n) { return n.id === link.source.id || n.id === link.target.id; });
                                
                                neighborNode.classed('neighbor-node', true);

                                d3.select("#link-" + link.source.id + "-" + link.target.id).classed('highlighted-link', true);
                            }

                        });

                        if (highlightedNode) {
                            highlightedNode.classed('hovered-node', false);
                        }

                        // Highlight the clicked node and update the highlightedNode variable
                        var currentNode = d3.select(this).classed('hovered-node', true);
                        highlightedNode = currentNode;

                    }

            var keyInfo = """

    string_6file=""";
            var links = [];
            matrix.forEach(function(row, i) {
                row.forEach(function(cell, j) {
                    if (cell === 1) {
                        links.push({ source: nodes[i].id, target: nodes[j].id });
                    }
                });
            });

            var simulation = d3.forceSimulation(nodes)
                .force("link", d3.forceLink(links).id(function(d) { return d.id; }))
                .force("charge", d3.forceManyBody())
                .force("center", d3.forceCenter(1200 / 2, 600 / 2)); // Coordinates based on the viewB


            var link = g.append("g")
                .attr("class", "links")
                .selectAll("line")
                .data(links)
                .enter()
                .append("line")
                .attr("id", function(d) { return "link-" + d.source.id + "-" + d.target.id; })

            var node = g.append("g")
                .attr("class", "nodes")
                .selectAll("circle")
                .data(nodes)
                .enter()
                .append("circle")
                .attr("r", 5)
                .attr("id", function(d) { return "node-" + d.id; })
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended))
                    .on("click", showNodeInfo);

            var labels = g.append("g")
                .attr("class", "nodetext")
                .selectAll("text")
                .data(nodes)
                .enter()
                .append("text")
                .text(function(d) { return d.id; })
                .style("visibility", "hidden");


            filterNodes('Clear');

            node.on("mouseover", function(d) {
                d3.select(this).classed('hovered-node', true);
                labels
                    .filter(function(node) { return node.id === d.id; })
                    .style("visibility", "visible");
            });

            node.on("mouseout", function(d) {
                if (highlightedNode && d.id === highlightedNode.id) {
                    return; // Do not remove the highlight if this is the currently selected node
                }

                
                d3.select(this).classed('hovered-node', false);
                labels
                    .filter(function(node) { return node.id === d.id; })
                    .style("visibility", "hidden");
            });

            simulation
                .nodes(nodes)
                .on("tick", ticked)
                .on("end", function() {
                });

            simulation.force("link")
                .links(links);

            function ticked() {
                link
                    .attr("x1", function(d) { return d.source.x; })
                    .attr("y1", function(d) { return d.source.y; })
                    .attr("x2", function(d) { return d.target.x; })
                    .attr("y2", function(d) { return d.target.y; });

                node
                    .attr("cx", function(d) { return d.x; })
                    .attr("cy", function(d) { return d.y; });

                labels
                    .attr("x", function(d) { return d.x + 8; })
                    .attr("y", function(d) { return d.y + 3; });
            }



            function dragstarted(d) {
                if (!d3.event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }

            function dragged(d) {
                d.fx = d3.event.x;
                d.fy = d3.event.y;
            }

            function dragended(d) {
                if (!d3.event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }

            svg.on("click", function() {
                d3.select("#tooltip").style("display", "none");            
                clearHighlights()
            });



            function searchNode() {
                var searchTerm = document.getElementById('node-search').value.toUpperCase();

                // Reset previous highlights
                clearHighlights();

                // Find and highlight the searched node
                var searchedNode = nodes.find(function (node) {
                    return node.id.toUpperCase() === searchTerm;
                });

                if (searchedNode) {
                    var escapedId = searchedNode.id.replace(/\./g, '\\\\.');
                    d3.select('#node-' + escapedId)
                        .classed('clicked-node', true);
                }
            }

            function filterNodes(metric) {
                // Reset all node colors first
                d3.selectAll('.nodes circle').style('fill', 'black'); // default color

                // Find the key pairs for the selected metric
                keyInfo.forEach(function(ki) {
                    if (ki.Operation === metric) {
                        ki["Nodes Set"].forEach(function(pair) {
                            pair.forEach(function(nodeId) {
                                var escapedId = nodeId.replace(/\./g, '\\\\.');
                                d3.select('#node-' + escapedId).style('fill', '#f44336'); // color for selected nodes
                            });
                        });
                    }
                });
            }


            // Update the event listener for the metric select dropdown
            document.getElementById('metric-select').addEventListener('change', function() {
                filterNodes(this.value);
                updateScoreDisplay(this.value);

            });

            function updateScoreDisplay(metric) {
                var scoreDisplay = document.getElementById('score-display');
                var score = keyInfo.find(ki => ki.Operation === metric)?.Score || '--';
                scoreDisplay.textContent = 'Score: ' + score;
            }


            document.getElementById('metric-select').addEventListener('change', function() {
                populateSetDropdown(this.value);
            });

            function highlightNodes(metric, setIndex) {
                // Reset all node colors first
                d3.selectAll('.nodes circle').style('fill', 'black'); // default color

                var selectedSet = keyInfo.find(ki => ki.Operation === metric)["Nodes Set"][setIndex];
                selectedSet.forEach(function(nodeId) {
                    d3.select('#node-' + nodeId.replace('.', '\\\\.')).style('fill', '#f44336'); 
                });
            }
            




            document.getElementById('set-select').addEventListener('change', function() {
                var metric = document.getElementById('metric-select').value;
                highlightNodes(metric, parseInt(this.value));
            });


            document.getElementById('node-search').addEventListener('keypress', function(event) {
                if (event.keyCode === 13) {
                    searchNode();
                }
            });





            
            
            function populateSetDropdown(metric) {
                var setSelect = document.getElementById('set-select');
                setSelect.innerHTML = ''; // Clear existing options

                var option = document.createElement("option");
                option.value = "";
                option.text = "Select the Nodes Set";
                option.disabled = true; // Disable this option
                option.selected = true; // Set as the default selected option
                setSelect.appendChild(option);

                keyInfo.forEach(function(ki) {
                    if (ki.Operation === metric) {
                        ki["Nodes Set"].forEach(function(pair, index) {
                            var option = document.createElement("option");
                            option.value = index;
                            option.text = pair.map(node => encodeURIComponent(node)).join(", ");
                            setSelect.appendChild(option);
                        });
                    }
                });
            }




            function downloadSVG() {
                // Create a new SVG element
                var cloneSvg = d3.select('body').append('svg')


                cloneSvg.selectAll('.links')
                    .data(link.data())
                    .enter()
                    .append('line')
                    .attr('x1', function(d) { return d.source.x; })
                    .attr('y1', function(d) { return d.source.y; })
                    .attr('x2', function(d) { return d.target.x; })
                    .attr('y2', function(d) { return d.target.y; })
                    .attr('stroke', function(d) {
                        // Applica lo stile della classe highlighted-link se presente
                        if (d3.select("#link-" + d.source.id + "-" + d.target.id).classed('highlighted-link')) {
                            return "#de5246"; // Colore specificato nella classe highlighted-link
                        } else {
                            return d3.select("#link-" + d.source.id + "-" + d.target.id).style("stroke");
                        }
                    })
                    .attr('stroke-opacity', 0.2)
                    .attr('stroke-width', 2);

                // Clona e appendi i nodi
                cloneSvg.selectAll('.nodes')
                    .data(node.data())
                    .enter()
                    .append('circle')
                    .attr('r', 5)
                    .attr('cx', function(d) { return d.x; })
                    .attr('cy', function(d) { return d.y; })
                    .attr('fill', function(d) { 
                        var originalNode = d3.select("#node-" + d.id);
                        var fillColor = originalNode.style("fill"); // Colore di default

                        // Applica il colore giallo se il nodo è cliccato
                        if (originalNode.classed('clicked-node')) {
                            fillColor = "#ffce44"; // Colore giallo specifico
                        }
                        
                        // Altri controlli possono essere inseriti qui se necessario

                        return fillColor;
                    });




                // Controlla se il toggle per le etichette è attivo
                if (document.getElementById('label-toggle').checked) {
                    // Clona e appendi le etichette dei nodi
                    cloneSvg.selectAll('.nodetext')
                        .data(labels.data())
                        .enter()
                        .append('text')
                        .text(function(d) { return d.id; })
                        .attr('x', function(d) { return d.x + 8; })
                        .attr('y', function(d) { return d.y + 3; })
                        .attr('visibility', 'visible');
                }

                // Calcola il bounding box del grafico
                var bbox = g.node().getBBox();

                // Definisci il margine desiderato
                var margin = 300; // Ad esempio, 50px di margine

                // Calcola le nuove dimensioni con il margine
                var newWidth = bbox.width + margin;
                var newHeight = bbox.height + margin;

                // Aggiusta il viewBox per centrare il grafico con un margine extra
                cloneSvg.attr('viewBox', `${bbox.x - margin / 2} ${bbox.y - margin / 2} ${newWidth} ${newHeight}`)


                // Serialize the new SVG
                var serializer = new XMLSerializer();
                var source = serializer.serializeToString(cloneSvg.node());

                // Create a Blob from the source
                var svgBlob = new Blob([source], {type: 'image/svg+xml;charset=utf-8'});
                var downloadLink = document.createElement('a');
                downloadLink.href = URL.createObjectURL(svgBlob);
                downloadLink.download = '"""


    final_string=string_1file+str(filename)+string_2file+info_net+string_3file+str_matrix+";"+string_4file+str_names+string_5file+df_string+string_6file+name_output+string_7file

    with open(outdir+"/"+filename+"_groupcentrality.html", 'w') as f:
        f.write(final_string)

