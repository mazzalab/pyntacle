import pandas as pd
import numpy as np
import json
import html



















#########################################################################################################################################################################################
#########################################################################################################################################################################################
#########################################################################################################################################################################################



# Rendering tiers for create_local_html, picked from the graph's own size so
# the browser is never handed an animated physics loop or a raw DOM/element
# count it can't keep smooth. Every tier still gets the full metrics table;
# only the interactive network view is scaled back (or dropped) as size grows.
_LOCAL_LIVE_MAX_NODES = 500     # <= this: continuously-animated force layout
_LOCAL_STATIC_MAX_NODES = 3000  # <= this: force layout is settled once, then frozen
_LOCAL_STATIC_MAX_EDGES = 8000  # either cap crossed -> network view skipped, table-only


def create_local_html(df_metrics, grafo, outdir):
	"""Write the interactive local-metrics report (<name>_local.html).

	The network is serialized as an edge list (O(E)), never a dense n x n
	adjacency matrix, so both the file size and the client-side link
	construction scale with the graph's actual edge count. Graphs beyond
	_LOCAL_STATIC_MAX_NODES/_LOCAL_STATIC_MAX_EDGES skip the interactive
	view entirely (table-only fallback) instead of handing the browser a
	network it can't render smoothly.
	"""
	n_nodes = grafo.vcount()
	n_edges = grafo.ecount()
	node_names = list(grafo.vs["name"])
	edges = grafo.get_edgelist()  # [(i, j), ...] vertex-index pairs, aligned to node_names
	metric_cols = [c for c in df_metrics.columns if c != "Node Name"]
	all_cols = ["Node Name"] + metric_cols

	# df_metrics.iterrows() index was never actually used below (the "Node
	# Name" column, always present, wins the dict merge) -- to_dict(records)
	# is the same data with the dead middleman removed.
	records = df_metrics.to_dict(orient="records")

	render_network = (n_nodes <= _LOCAL_STATIC_MAX_NODES) and (n_edges <= _LOCAL_STATIC_MAX_EDGES)
	live_animated = render_network and (n_nodes <= _LOCAL_LIVE_MAX_NODES)

	# grafo.removed is None or a list of names; wrapping it in a Python set
	# literal (the old `str({grafo.removed})`) raised "unhashable type: list"
	# any time -r/--remove was combined with the local command.
	info_items = (
		"<li>Removed nodes: " + str(grafo.removed) + "</li>"
		"<li>Number of components: " + str(len(grafo.components())) + "</li>"
		"<li>Number of Nodes: " + str(n_nodes) + "</li>"
		"<li>Number of Edges: " + str(n_edges) + "</li>"
	)

	name_output = str(grafo.name) + ".svg"

	head = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Local Metrics Report</title>
    <script src="https://d3js.org/d3.v5.min.js"></script>
    <style>
:root{
  --bg:#f4f6f8; --surface:#ffffff; --border:#e0e4e8;
  --accent:#00796b; --accent-soft:#e0f2f1; --text:#1f2937; --text-soft:#5f6b7a;
  --radius:12px; --shadow:0 2px 8px rgba(15,23,42,.08);
}
*{box-sizing:border-box;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);}
.topbar{display:flex;align-items:center;gap:.75rem;padding:.75rem 1.25rem;background:var(--surface);border-bottom:1px solid var(--border);box-shadow:var(--shadow);}
.topbar img{height:36px;}
.topbar h1{font-size:1.05rem;margin:0;font-weight:600;color:var(--accent);}
.app-shell{display:grid;grid-template-columns:1fr 360px;gap:1rem;padding:1rem;align-items:start;}
@media (max-width:900px){.app-shell{grid-template-columns:1fr;}}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);padding:1rem;margin-bottom:1rem;}
.panel h2{font-size:.85rem;text-transform:uppercase;letter-spacing:.04em;color:var(--accent);margin:0 0 .75rem 0;font-weight:700;}
.graph-toolbar{display:flex;flex-wrap:wrap;gap:.9rem;align-items:center;padding:.25rem .25rem .75rem;}
svg#network{width:100%;height:70vh;background:var(--surface);border-radius:var(--radius);}
.btn-modern{border:none;border-radius:8px;padding:.4rem .9rem;font-size:.85rem;font-weight:600;background:var(--accent);color:#fff;cursor:pointer;transition:background .15s ease;}
.btn-modern:hover{background:#00695c;}
.field-row{display:flex;gap:.5rem;margin-bottom:.6rem;align-items:center;flex-wrap:wrap;}
input[type=text],input[type=number]{border:1px solid var(--border);border-radius:6px;padding:.35rem .5rem;font-size:.85rem;}
input.search-not-found{box-shadow:0 0 0 2px #de5246;}
select{border:1px solid var(--border);border-radius:6px;padding:.35rem .5rem;font-size:.85rem;}
.switch{position:relative;display:inline-block;width:34px;height:18px;}
.switch input{opacity:0;width:0;height:0;}
.slider-toggle{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background:#ccd3d9;transition:.2s;border-radius:34px;}
.slider-toggle:before{position:absolute;content:"";height:14px;width:14px;left:2px;bottom:2px;background:#fff;transition:.2s;border-radius:50%;}
input:checked+.slider-toggle{background:var(--accent);}
input:checked+.slider-toggle:before{transform:translateX(16px);}
.toggle-label{font-size:.82rem;color:var(--text-soft);margin-right:.3rem;}
.range-row{display:flex;flex-direction:column;gap:.3rem;margin-bottom:.5rem;}
.range-row label{font-size:.78rem;color:var(--text-soft);}
ul.overview-list{list-style:none;margin:0;padding:0;font-size:.85rem;color:var(--text-soft);}
ul.overview-list li{padding:.15rem 0;}
.node-popup{position:fixed;min-width:220px;max-width:280px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:0 8px 24px rgba(15,23,42,.18);padding:.75rem .9rem;font-size:.82rem;display:none;z-index:1000;}
.node-popup h3{margin:0 0 .4rem 0;font-size:.9rem;color:var(--accent);padding-right:1rem;}
.node-popup .popup-close{position:absolute;top:.4rem;right:.6rem;cursor:pointer;color:var(--text-soft);font-weight:700;}
.node-popup table{width:100%;border-collapse:collapse;}
.node-popup td{padding:.15rem 0;border-bottom:1px dashed var(--border);}
.node-popup td:first-child{color:var(--text-soft);}
.warning-banner{background:#fff8e1;border:1px solid #ffe082;color:#8d6e00;border-radius:var(--radius);padding:.85rem 1rem;margin-bottom:1rem;font-size:.9rem;}
.links line{stroke:#9aa5b1;stroke-opacity:.55;}
.nodes circle{stroke:#fff;stroke-width:1.2px;fill:#3f7cac;}
.nodetext text{font-size:11px;fill:var(--text);}
.hovered-node{fill:#ffce44 !important;}
.clicked-node{fill:#ffce44 !important;}
.neighbor-node{fill:#de5246 !important;}
.highlighted-link{stroke:#de5246 !important;stroke-opacity:.5 !important;stroke-width:2px;}
table.metrics-table{width:100%;border-collapse:collapse;font-size:.82rem;}
table.metrics-table th,table.metrics-table td{padding:.4rem .5rem;border-bottom:1px solid var(--border);text-align:left;}
table.metrics-table th{cursor:pointer;color:var(--accent);white-space:nowrap;}
    </style>
</head>
<body>
<div class="topbar">
    <img src="https://camo.githubusercontent.com/21117091dc0315536e4ad1ccf7548c87c4626bc3563c1c96e3b40430114a3ae5/687474703a2f2f70796e7461636c652e6373732d6d656e64656c2e69742f696d616765732f7469746c655f6a6f696e65642e706e67">
    <h1>Local Metrics Report &mdash; """ + str(grafo.name) + """</h1>
</div>
<div class="app-shell">
<div>
"""

	sidebar_overview = """
<div class="panel">
    <h2>Network Overview</h2>
    <ul class="overview-list">""" + info_items + """</ul>
</div>
"""

	if render_network:
		warning_html = ""
		main_panel = """
<div class="panel">
    <div class="graph-toolbar">
        <button id="export-svg-btn" class="btn-modern">Export SVG</button>
        <button id="export-png-btn" class="btn-modern">Export PNG</button>
        <span class="toggle-label">Node labels</span>
        <label class="switch"><input type="checkbox" id="label-toggle"><span class="slider-toggle"></span></label>
        <span class="toggle-label">Edges</span>
        <label class="switch"><input type="checkbox" id="edge-toggle" checked><span class="slider-toggle"></span></label>
    </div>
    <div id="box-to-export">
        <svg id="network" viewBox="0 0 1200 700" preserveAspectRatio="xMidYMid meet"></svg>
    </div>
</div>
"""
		sidebar_controls = """
<div class="panel">
    <h2>Search</h2>
    <div class="field-row">
        <input type="text" id="node-search" placeholder="Node name">
        <button id="search-btn" class="btn-modern">Find</button>
        <button id="search-clear" class="btn-modern" style="background:var(--accent-soft);color:var(--accent);">Clear</button>
    </div>
</div>
<div class="panel">
    <h2>Filter by metric</h2>
    <div class="field-row">
        <select id="metric-select">""" + "".join(
			'<option value="{0}">{0}</option>'.format(m) for m in metric_cols
		) + """</select>
    </div>
    <div class="range-row">
        <label>Minimum</label>
        <input type="range" id="metric-min" style="width:100%;">
    </div>
    <div class="range-row">
        <label>Maximum</label>
        <input type="range" id="metric-max" style="width:100%;">
    </div>
    <div id="range-readout" style="font-size:.8rem;color:var(--text-soft);"></div>
</div>
"""
		popup_html = """
<div id="node-popup" class="node-popup">
    <span class="popup-close" id="popup-close">&times;</span>
    <h3 id="popup-title"></h3>
    <table><tbody id="popup-body"></tbody></table>
</div>
"""
		table_html = ""
	else:
		warning_html = (
			'<div class="warning-banner">This network has ' + str(n_nodes) + ' nodes and '
			+ str(n_edges) + ' edges, above the practical limit for a smooth interactive layout '
			'(' + str(_LOCAL_STATIC_MAX_NODES) + ' nodes / ' + str(_LOCAL_STATIC_MAX_EDGES) + ' edges). '
			'Showing the metrics table only &mdash; no network view was built.</div>'
		)
		main_panel = """
<div class="panel">
    <h2>Metrics table</h2>
    <div class="field-row"><input type="text" id="table-search" placeholder="Filter by node name" style="width:100%;"></div>
    <div style="overflow-x:auto;max-height:75vh;">
    <table class="metrics-table" id="metrics-table">
        <thead><tr>""" + "".join("<th>{0}</th>".format(c) for c in all_cols) + """</tr></thead>
        <tbody></tbody>
    </table>
    </div>
</div>
"""
		sidebar_controls = ""
		popup_html = ""
		table_html = ""

	body_top = head + warning_html + main_panel + "</div><div>" + sidebar_overview + sidebar_controls + "</div></div>" + popup_html + table_html

	script_open = """
<script>
"""

	if render_network:
		script_body = """
(function(){
var NODE_NAMES = """ + json.dumps(node_names) + """;
var EDGES = """ + json.dumps(edges) + """;
var METRICS = """ + json.dumps(records) + """;
var METRIC_COLS = """ + json.dumps(metric_cols) + """;
var LIVE_ANIMATED = """ + ("true" if live_animated else "false") + """;
var DOWNLOAD_NAME = """ + json.dumps(name_output) + """;

// O(1) lookup instead of Array.find(): with an O(n) scan called once per
// node on every filter/slider event, filtering was effectively O(n^2).
var metricsById = new Map(METRICS.map(function(d){ return [d["Node Name"], d]; }));

var nodes = NODE_NAMES.map(function(name){ return { id: name }; });
var links = EDGES.map(function(e){ return { source: nodes[e[0]].id, target: nodes[e[1]].id }; });

var NODE_RADIUS = 6; // fixed for every node -- size must not imply a metric

var svg = d3.select("#network");
var viewBoxParts = svg.attr("viewBox").split(" ").map(Number);
var width = viewBoxParts[2], height = viewBoxParts[3];

var g = svg.append("g");
svg.call(d3.zoom().scaleExtent([0.2, 12]).on("zoom", function(){ g.attr("transform", d3.event.transform); }));

var link = g.append("g").attr("class", "links").selectAll("line")
    .data(links).enter().append("line")
    .attr("id", function(d){ return "link-" + d.source + "-" + d.target; });

var node = g.append("g").attr("class", "nodes").selectAll("circle")
    .data(nodes).enter().append("circle")
    .attr("r", NODE_RADIUS)
    .attr("id", function(d){ return "node-" + d.id; })
    .on("click", showNodeInfo)
    .call(d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended));

var labels = g.append("g").attr("class", "nodetext").selectAll("text")
    .data(nodes).enter().append("text")
    .text(function(d){ return d.id; })
    .style("visibility", "hidden");

var labelsOn = false, edgesOn = true, highlightedNode = null;
var visibleIds = new Set(nodes.map(function(d){ return d.id; }));

function nodeVisible(id){ return visibleIds.has(id); }
function linkEndpointId(x){ return (x && typeof x === "object") ? x.id : x; }
function linkVisible(l){ return edgesOn && nodeVisible(linkEndpointId(l.source)) && nodeVisible(linkEndpointId(l.target)); }

function refreshVisibility(){
    node.style("display", function(d){ return nodeVisible(d.id) ? null : "none"; });
    link.style("display", function(d){ return linkVisible(d) ? null : "none"; });
    labels.style("visibility", function(d){ return (labelsOn && nodeVisible(d.id)) ? "visible" : "hidden"; });
}

var simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(function(d){ return d.id; }).distance(40))
    .force("charge", d3.forceManyBody().strength(-60))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide(8));

function ticked(){
    link.attr("x1", function(d){ return d.source.x; }).attr("y1", function(d){ return d.source.y; })
        .attr("x2", function(d){ return d.target.x; }).attr("y2", function(d){ return d.target.y; });
    node.attr("cx", function(d){ return d.x; }).attr("cy", function(d){ return d.y; });
    labels.attr("x", function(d){ return d.x + 8; }).attr("y", function(d){ return d.y + 3; });
}

if (LIVE_ANIMATED) {
    simulation.on("tick", ticked);
} else {
    // Medium graphs: settle the layout once, synchronously, instead of
    // paying for a physics loop the tab would have to keep alive forever.
    simulation.stop();
    var settleTicks = Math.min(300, Math.ceil(Math.log(nodes.length + 1) * 60));
    for (var i = 0; i < settleTicks; i++) simulation.tick();
    ticked();
}
refreshVisibility();

function dragstarted(d){
    if (LIVE_ANIMATED && !d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x; d.fy = d.y;
}
function dragged(d){
    d.fx = d3.event.x; d.fy = d3.event.y;
    if (!LIVE_ANIMATED) { d.x = d.fx; d.y = d.fy; ticked(); }
}
function dragended(d){
    if (LIVE_ANIMATED && !d3.event.active) simulation.alphaTarget(0);
    d.fx = null; d.fy = null;
}

node.on("mouseover", function(d){
    d3.select(this).classed("hovered-node", true);
    labels.filter(function(l){ return l.id === d.id; }).style("visibility", "visible");
}).on("mouseout", function(d){
    if (highlightedNode === d.id) return;
    d3.select(this).classed("hovered-node", false);
    labels.filter(function(l){ return l.id === d.id; })
        .style("visibility", (labelsOn && nodeVisible(d.id)) ? "visible" : "hidden");
});

function clearHighlights(){
    // .hovered-node is deliberately left set by mouseout while a node is the
    // active selection (see the early-return above) -- must be cleared here too,
    // or the yellow fill sticks around after the mouse has long since left.
    d3.selectAll(".nodes circle").classed("clicked-node", false).classed("neighbor-node", false).classed("hovered-node", false);
    d3.selectAll(".links line").classed("highlighted-link", false);
    highlightedNode = null;
}

function closePopup(){ document.getElementById("node-popup").style.display = "none"; }
document.getElementById("popup-close").addEventListener("click", closePopup);

function showNodeInfo(d){
    d3.event.stopPropagation();
    clearHighlights();
    d3.select(this).classed("clicked-node", true);
    highlightedNode = d.id;

    links.forEach(function(l){
        var sid = linkEndpointId(l.source), tid = linkEndpointId(l.target);
        if (sid === d.id || tid === d.id) {
            d3.selectAll(".nodes circle").filter(function(n){ return n.id === sid || n.id === tid; })
                .classed("neighbor-node", true);
            d3.select("#link-" + sid + "-" + tid).classed("highlighted-link", true);
        }
    });

    var info = metricsById.get(d.id);
    if (!info) return;
    document.getElementById("popup-title").textContent = info["Node Name"];
    var tbody = document.getElementById("popup-body");
    tbody.innerHTML = "";
    METRIC_COLS.forEach(function(m){
        var tr = document.createElement("tr");
        var tdKey = document.createElement("td"); tdKey.textContent = m;
        var tdVal = document.createElement("td"); tdVal.textContent = info[m];
        tr.appendChild(tdKey); tr.appendChild(tdVal);
        tbody.appendChild(tr);
    });

    var popup = document.getElementById("node-popup");
    var x = Math.min(d3.event.pageX + 12, window.innerWidth - 300);
    var y = Math.min(d3.event.pageY + 12, window.innerHeight - 200);
    popup.style.left = x + "px"; popup.style.top = y + "px"; popup.style.display = "block";
}

svg.on("click", function(){ closePopup(); clearHighlights(); });

function searchNode(){
    var term = document.getElementById("node-search").value.trim();
    closePopup(); clearHighlights();
    if (!term) return;
    var match = nodes.find(function(n){ return n.id.toUpperCase() === term.toUpperCase(); });
    var input = document.getElementById("node-search");
    if (match) {
        d3.select("#node-" + match.id).classed("clicked-node", true);
        input.classList.remove("search-not-found");
    } else {
        input.classList.add("search-not-found");
        setTimeout(function(){ input.classList.remove("search-not-found"); }, 600);
    }
}
document.getElementById("node-search").addEventListener("keypress", function(e){ if (e.keyCode === 13) searchNode(); });
document.getElementById("search-btn").addEventListener("click", searchNode);
document.getElementById("search-clear").addEventListener("click", function(){
    document.getElementById("node-search").value = ""; closePopup(); clearHighlights();
});

document.getElementById("label-toggle").addEventListener("change", function(){ labelsOn = this.checked; refreshVisibility(); });
document.getElementById("edge-toggle").addEventListener("change", function(){ edgesOn = this.checked; refreshVisibility(); });

var metricSelect = document.getElementById("metric-select");
var minInput = document.getElementById("metric-min");
var maxInput = document.getElementById("metric-max");

function metricRange(metric){
    var vals = METRICS.map(function(d){ return +d[metric]; }).filter(function(v){ return !isNaN(v); });
    return [Math.min.apply(null, vals), Math.max.apply(null, vals)];
}

function resetRangeInputs(){
    var range = metricRange(metricSelect.value);
    var step = (range[1] - range[0]) / 100 || 1;
    [minInput, maxInput].forEach(function(inp){ inp.min = range[0]; inp.max = range[1]; inp.step = step; });
    minInput.value = range[0]; maxInput.value = range[1];
    applyFilter();
}

function applyFilter(){
    var metric = metricSelect.value;
    var lo = +minInput.value, hi = +maxInput.value;
    if (lo > hi) { var t = lo; lo = hi; hi = t; }
    document.getElementById("range-readout").textContent = lo.toFixed(2) + " – " + hi.toFixed(2);

    visibleIds = new Set(METRICS.filter(function(d){
        var v = +d[metric];
        return !isNaN(v) && v >= lo && v <= hi;
    }).map(function(d){ return d["Node Name"]; }));

    refreshVisibility();
}

metricSelect.addEventListener("change", resetRangeInputs);
minInput.addEventListener("input", applyFilter);
maxInput.addEventListener("input", applyFilter);
resetRangeInputs();

function buildVisibleClone(){
    var clone = d3.select(document.body).append("svg").attr("xmlns", "http://www.w3.org/2000/svg");
    var visibleNodes = nodes.filter(function(d){ return nodeVisible(d.id); });
    var visibleLinks = links.filter(linkVisible);

    clone.append("g").selectAll("line").data(visibleLinks).enter().append("line")
        .attr("x1", function(d){ return d.source.x; }).attr("y1", function(d){ return d.source.y; })
        .attr("x2", function(d){ return d.target.x; }).attr("y2", function(d){ return d.target.y; })
        .attr("stroke", function(d){
            var live = d3.select("#link-" + linkEndpointId(d.source) + "-" + linkEndpointId(d.target));
            return live.classed("highlighted-link") ? "#de5246" : "#9aa5b1";
        })
        .attr("stroke-opacity", 0.5).attr("stroke-width", 2);

    clone.append("g").selectAll("circle").data(visibleNodes).enter().append("circle")
        .attr("r", function(d){ return d3.select("#node-" + d.id).attr("r"); })
        .attr("cx", function(d){ return d.x; }).attr("cy", function(d){ return d.y; })
        .attr("fill", function(d){
            var live = d3.select("#node-" + d.id);
            if (live.classed("clicked-node")) return "#ffce44";
            if (live.classed("neighbor-node")) return "#de5246";
            return "#3f7cac";
        });

    if (labelsOn) {
        clone.append("g").selectAll("text").data(visibleNodes).enter().append("text")
            .text(function(d){ return d.id; })
            .attr("x", function(d){ return d.x + 8; }).attr("y", function(d){ return d.y + 3; });
    }

    var bbox = clone.node().getBBox();
    var margin = 40;
    clone.attr("viewBox", (bbox.x - margin / 2) + " " + (bbox.y - margin / 2) + " " + (bbox.width + margin) + " " + (bbox.height + margin))
         .attr("width", bbox.width + margin).attr("height", bbox.height + margin);
    return clone.node();
}

function triggerDownload(href, filename){
    var a = document.createElement("a");
    a.href = href; a.download = filename;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
}

function downloadSVG(){
    var clone = buildVisibleClone();
    var source = new XMLSerializer().serializeToString(clone);
    var blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
    triggerDownload(URL.createObjectURL(blob), DOWNLOAD_NAME);
    clone.remove();
}

function downloadPNG(){
    var clone = buildVisibleClone();
    var source = new XMLSerializer().serializeToString(clone);
    var url = URL.createObjectURL(new Blob([source], { type: "image/svg+xml;charset=utf-8" }));
    var img = new Image();
    img.onload = function(){
        var scale = 2; // rasterize at 2x for a crisper PNG than the on-screen SVG
        var canvas = document.createElement("canvas");
        canvas.width = img.width * scale; canvas.height = img.height * scale;
        var ctx = canvas.getContext("2d");
        ctx.fillStyle = "#ffffff"; ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.scale(scale, scale); ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(url);
        canvas.toBlob(function(pngBlob){
            triggerDownload(URL.createObjectURL(pngBlob), DOWNLOAD_NAME.replace(/\\.svg$/, ".png"));
        });
        clone.remove();
    };
    img.onerror = function(){ alert("PNG export failed while rasterizing the network snapshot."); clone.remove(); };
    img.src = url;
}

document.getElementById("export-svg-btn").addEventListener("click", downloadSVG);
document.getElementById("export-png-btn").addEventListener("click", downloadPNG);
})();
"""
	else:
		script_body = """
(function(){
var METRICS = """ + json.dumps(records) + """;
var COLS = """ + json.dumps(all_cols) + """;
var table = document.getElementById("metrics-table");
var tbody = table.querySelector("tbody");

function render(rows){
    tbody.innerHTML = "";
    rows.forEach(function(r){
        var tr = document.createElement("tr");
        COLS.forEach(function(c){
            var td = document.createElement("td"); td.textContent = r[c]; tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
}
render(METRICS);

document.getElementById("table-search").addEventListener("input", function(){
    var term = this.value.toLowerCase();
    render(METRICS.filter(function(r){ return String(r["Node Name"]).toLowerCase().indexOf(term) !== -1; }));
});

var sortState = { col: null, asc: true };
Array.prototype.forEach.call(table.querySelectorAll("th"), function(th, idx){
    th.addEventListener("click", function(){
        var col = COLS[idx];
        sortState.asc = (sortState.col === col) ? !sortState.asc : true;
        sortState.col = col;
        var sorted = METRICS.slice().sort(function(a, b){
            var va = a[col], vb = b[col];
            if (typeof va === "number" && typeof vb === "number") return sortState.asc ? va - vb : vb - va;
            return sortState.asc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
        });
        render(sorted);
    });
});
})();
"""

	script_close = """
</script>
</body>
</html>
"""

	final_string = body_top + script_open + script_body + script_close

	with open(outdir + "/" + grafo.name + "_local.html", 'w') as f:
	    f.write(final_string)




































#######################################################################################################################################################################
#######################################################################################################################################################################
#######################################################################################################################################################################
#######################################################################################################################################################################


# Rendering tiers for create_keyplayer_html -- same rationale as the local
# report: large graphs get a table-only fallback instead of an animated
# force layout the browser can't keep up with.
_KP_LIVE_MAX_NODES = 500
_KP_STATIC_MAX_NODES = 3000
_KP_STATIC_MAX_EDGES = 8000


def create_keyplayer_html(df_metrics, grafo, outdir, filename):
    """Write the interactive keyplayer report (<filename>_keyplayer.html).

    df_metrics must have exactly the columns Operation/KeySet/Score, one row
    per key-player metric -- KeySet is a plain list of node names. Every
    algorithm in this codebase (brute force, greedy, gradient descent)
    returns exactly one optimal set per metric, never several candidates,
    so there is nothing to browse beyond picking the metric itself.

    The network is serialized as an edge list (O(E)), never a dense n x n
    adjacency matrix, mirroring the local-metrics report's fix for the same
    memory/CPU wall.
    """
    n_nodes = grafo.vcount()
    n_edges = grafo.ecount()
    node_names = list(grafo.vs["name"])
    edges = grafo.get_edgelist()
    records = df_metrics.to_dict(orient="records")
    operations = [r["Operation"] for r in records]

    render_network = (n_nodes <= _KP_STATIC_MAX_NODES) and (n_edges <= _KP_STATIC_MAX_EDGES)
    live_animated = render_network and (n_nodes <= _KP_LIVE_MAX_NODES)

    # grafo.removed is None or a list of names; the old `str({grafo.removed})`
    # wrapped it in a Python set literal, which raised "unhashable type: list".
    info_items = (
        "<li>Removed nodes: " + str(grafo.removed) + "</li>"
        "<li>Number of components: " + str(len(grafo.components())) + "</li>"
        "<li>Number of Nodes: " + str(n_nodes) + "</li>"
        "<li>Number of Edges: " + str(n_edges) + "</li>"
    )

    name_output = str(filename) + ".svg"

    head = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Key Player Report</title>
    <script src="https://d3js.org/d3.v5.min.js"></script>
    <style>
:root{
  --bg:#f4f6f8; --surface:#ffffff; --border:#e0e4e8;
  --accent:#00796b; --accent-soft:#e0f2f1; --text:#1f2937; --text-soft:#5f6b7a;
  --radius:12px; --shadow:0 2px 8px rgba(15,23,42,.08);
}
*{box-sizing:border-box;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);}
.topbar{display:flex;align-items:center;gap:.75rem;padding:.75rem 1.25rem;background:var(--surface);border-bottom:1px solid var(--border);box-shadow:var(--shadow);}
.topbar img{height:36px;}
.topbar h1{font-size:1.05rem;margin:0;font-weight:600;color:var(--accent);}
.app-shell{display:grid;grid-template-columns:1fr 360px;gap:1rem;padding:1rem;align-items:start;}
@media (max-width:900px){.app-shell{grid-template-columns:1fr;}}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);padding:1rem;margin-bottom:1rem;}
.panel h2{font-size:.85rem;text-transform:uppercase;letter-spacing:.04em;color:var(--accent);margin:0 0 .75rem 0;font-weight:700;}
.graph-toolbar{display:flex;flex-wrap:wrap;gap:.9rem;align-items:center;padding:.25rem .25rem .75rem;}
svg#network{width:100%;height:70vh;background:var(--surface);border-radius:var(--radius);}
.btn-modern{border:none;border-radius:8px;padding:.4rem .9rem;font-size:.85rem;font-weight:600;background:var(--accent);color:#fff;cursor:pointer;transition:background .15s ease;}
.btn-modern:hover{background:#00695c;}
.field-row{display:flex;gap:.5rem;margin-bottom:.6rem;align-items:center;flex-wrap:wrap;}
input[type=text]{border:1px solid var(--border);border-radius:6px;padding:.35rem .5rem;font-size:.85rem;}
input.search-not-found{box-shadow:0 0 0 2px #de5246;}
select{border:1px solid var(--border);border-radius:6px;padding:.35rem .5rem;font-size:.85rem;}
.switch{position:relative;display:inline-block;width:34px;height:18px;}
.switch input{opacity:0;width:0;height:0;}
.slider-toggle{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background:#ccd3d9;transition:.2s;border-radius:34px;}
.slider-toggle:before{position:absolute;content:"";height:14px;width:14px;left:2px;bottom:2px;background:#fff;transition:.2s;border-radius:50%;}
input:checked+.slider-toggle{background:var(--accent);}
input:checked+.slider-toggle:before{transform:translateX(16px);}
.toggle-label{font-size:.82rem;color:var(--text-soft);margin-right:.3rem;}
ul.overview-list{list-style:none;margin:0;padding:0;font-size:.85rem;color:var(--text-soft);}
ul.overview-list li{padding:.15rem 0;}
.kp-readout{font-size:.85rem;color:var(--text-soft);}
.kp-readout b{color:var(--text);}
.kp-score{font-weight:700;color:var(--accent);}
.warning-banner{background:#fff8e1;border:1px solid #ffe082;color:#8d6e00;border-radius:var(--radius);padding:.85rem 1rem;margin-bottom:1rem;font-size:.9rem;}
.links line{stroke:#9aa5b1;stroke-opacity:.55;}
.nodes circle{stroke:#fff;stroke-width:1.2px;fill:#3f7cac;}
.nodetext text{font-size:11px;fill:var(--text);}
.hovered-node{fill:#ffce44 !important;}
.clicked-node{fill:#ffce44 !important;}
.neighbor-node{fill:#de5246 !important;}
.keyplayer-node{fill:#f44336 !important;}
.highlighted-link{stroke:#de5246 !important;stroke-opacity:.5 !important;stroke-width:2px;}
table.metrics-table{width:100%;border-collapse:collapse;font-size:.82rem;}
table.metrics-table th,table.metrics-table td{padding:.4rem .5rem;border-bottom:1px solid var(--border);text-align:left;}
    </style>
</head>
<body>
<div class="topbar">
    <img src="https://camo.githubusercontent.com/21117091dc0315536e4ad1ccf7548c87c4626bc3563c1c96e3b40430114a3ae5/687474703a2f2f70796e7461636c652e6373732d6d656e64656c2e69742f696d616765732f7469746c655f6a6f696e65642e706e67">
    <h1>Key Player Report &mdash; """ + html.escape(str(filename)) + """</h1>
</div>
<div class="app-shell">
<div>
"""

    sidebar_overview = """
<div class="panel">
    <h2>Network Overview</h2>
    <ul class="overview-list">""" + info_items + """</ul>
</div>
"""

    if render_network:
        warning_html = ""
        main_panel = """
<div class="panel">
    <div class="graph-toolbar">
        <button id="export-svg-btn" class="btn-modern">Export SVG</button>
        <button id="export-png-btn" class="btn-modern">Export PNG</button>
        <span class="toggle-label">Node labels</span>
        <label class="switch"><input type="checkbox" id="label-toggle"><span class="slider-toggle"></span></label>
        <span class="toggle-label">Edges</span>
        <label class="switch"><input type="checkbox" id="edge-toggle" checked><span class="slider-toggle"></span></label>
    </div>
    <div id="box-to-export">
        <svg id="network" viewBox="0 0 1200 700" preserveAspectRatio="xMidYMid meet"></svg>
    </div>
</div>
"""
        sidebar_controls = """
<div class="panel">
    <h2>Search</h2>
    <div class="field-row">
        <input type="text" id="node-search" placeholder="Node name">
        <button id="search-btn" class="btn-modern">Find</button>
        <button id="search-clear" class="btn-modern" style="background:var(--accent-soft);color:var(--accent);">Clear</button>
    </div>
</div>
<div class="panel">
    <h2>Key player metric</h2>
    <div class="field-row">
        <select id="metric-select">""" + "".join(
            '<option value="{0}">{0}</option>'.format(html.escape(str(op))) for op in operations
        ) + """</select>
    </div>
    <div class="field-row" id="tie-row" style="display:none;">
        <select id="set-select"></select>
    </div>
    <p class="kp-readout" id="tie-note"></p>
    <p class="kp-readout">Score: <span id="score-display" class="kp-score">--</span></p>
    <p class="kp-readout"><b>Key player set:</b> <span id="set-display">--</span></p>
</div>
"""
        table_html = ""
    else:
        warning_html = (
            '<div class="warning-banner">This network has ' + str(n_nodes) + ' nodes and '
            + str(n_edges) + ' edges, above the practical limit for a smooth interactive layout '
            '(' + str(_KP_STATIC_MAX_NODES) + ' nodes / ' + str(_KP_STATIC_MAX_EDGES) + ' edges). '
            'Showing the key player sets as a table only &mdash; no network view was built.</div>'
        )
        rows_html = "".join(
            "<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>".format(
                html.escape(str(r["Operation"])),
                html.escape(str(r["Score"])),
                html.escape(", ".join(str(x) for x in r["KeySet"])),
            ) for r in records
        )
        main_panel = """
<div class="panel">
    <h2>Key player sets</h2>
    <div style="overflow-x:auto;">
    <table class="metrics-table">
        <thead><tr><th>Operation</th><th>Score</th><th>Key player set</th></tr></thead>
        <tbody>""" + rows_html + """</tbody>
    </table>
    </div>
</div>
"""
        sidebar_controls = ""
        table_html = ""

    body_top = (
        head + warning_html + main_panel + "</div><div>" + sidebar_overview
        + sidebar_controls + "</div></div>" + table_html
    )

    if render_network:
        script_open = "\n<script>\n"
        script_body = """
(function(){
var NODE_NAMES = """ + json.dumps(node_names) + """;
var EDGES = """ + json.dumps(edges) + """;
var KEYINFO = """ + json.dumps(records) + """;
var LIVE_ANIMATED = """ + ("true" if live_animated else "false") + """;
var DOWNLOAD_NAME = """ + json.dumps(name_output) + """;

var keyInfoByOp = new Map(KEYINFO.map(function(d){ return [d.Operation, d]; }));

var nodes = NODE_NAMES.map(function(name){ return { id: name }; });
var links = EDGES.map(function(e){ return { source: nodes[e[0]].id, target: nodes[e[1]].id }; });

var NODE_RADIUS = 6;

var svg = d3.select("#network");
var viewBoxParts = svg.attr("viewBox").split(" ").map(Number);
var width = viewBoxParts[2], height = viewBoxParts[3];

var g = svg.append("g");
svg.call(d3.zoom().scaleExtent([0.2, 12]).on("zoom", function(){ g.attr("transform", d3.event.transform); }));

var link = g.append("g").attr("class", "links").selectAll("line")
    .data(links).enter().append("line")
    .attr("id", function(d){ return "link-" + d.source + "-" + d.target; });

var node = g.append("g").attr("class", "nodes").selectAll("circle")
    .data(nodes).enter().append("circle")
    .attr("r", NODE_RADIUS)
    .attr("id", function(d){ return "node-" + d.id; })
    .on("click", showNodeInfo)
    .call(d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended));

var labels = g.append("g").attr("class", "nodetext").selectAll("text")
    .data(nodes).enter().append("text")
    .text(function(d){ return d.id; })
    .style("visibility", "hidden");

var labelsOn = false, edgesOn = true, highlightedNode = null, currentKeySet = new Set();

function linkEndpointId(x){ return (x && typeof x === "object") ? x.id : x; }

function refreshVisibility(){
    link.style("display", function(){ return edgesOn ? null : "none"; });
    labels.style("visibility", function(){ return labelsOn ? "visible" : "hidden"; });
}

var simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(function(d){ return d.id; }).distance(40))
    .force("charge", d3.forceManyBody().strength(-60))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide(8));

function ticked(){
    link.attr("x1", function(d){ return d.source.x; }).attr("y1", function(d){ return d.source.y; })
        .attr("x2", function(d){ return d.target.x; }).attr("y2", function(d){ return d.target.y; });
    node.attr("cx", function(d){ return d.x; }).attr("cy", function(d){ return d.y; });
    labels.attr("x", function(d){ return d.x + 8; }).attr("y", function(d){ return d.y + 3; });
}

if (LIVE_ANIMATED) {
    simulation.on("tick", ticked);
} else {
    // Medium graphs: settle the layout once, synchronously, instead of
    // paying for a physics loop the tab would have to keep alive forever.
    simulation.stop();
    var settleTicks = Math.min(300, Math.ceil(Math.log(nodes.length + 1) * 60));
    for (var i = 0; i < settleTicks; i++) simulation.tick();
    ticked();
}
refreshVisibility();

function dragstarted(d){
    if (LIVE_ANIMATED && !d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x; d.fy = d.y;
}
function dragged(d){
    d.fx = d3.event.x; d.fy = d3.event.y;
    if (!LIVE_ANIMATED) { d.x = d.fx; d.y = d.fy; ticked(); }
}
function dragended(d){
    if (LIVE_ANIMATED && !d3.event.active) simulation.alphaTarget(0);
    d.fx = null; d.fy = null;
}

node.on("mouseover", function(d){
    d3.select(this).classed("hovered-node", true);
    labels.filter(function(l){ return l.id === d.id; }).style("visibility", "visible");
}).on("mouseout", function(d){
    if (highlightedNode === d.id) return;
    d3.select(this).classed("hovered-node", false);
    labels.filter(function(l){ return l.id === d.id; })
        .style("visibility", labelsOn ? "visible" : "hidden");
});

function clearClickHighlight(){
    // .hovered-node can be left set by mouseout's early-return above while a
    // node is the active selection -- must be cleared here too, or the
    // yellow fill sticks around after the mouse has long since left.
    d3.selectAll(".nodes circle").classed("clicked-node", false).classed("neighbor-node", false).classed("hovered-node", false);
    d3.selectAll(".links line").classed("highlighted-link", false);
    highlightedNode = null;
}

function showNodeInfo(d){
    d3.event.stopPropagation();
    clearClickHighlight();
    d3.select(this).classed("clicked-node", true);
    highlightedNode = d.id;

    links.forEach(function(l){
        var sid = linkEndpointId(l.source), tid = linkEndpointId(l.target);
        if (sid === d.id || tid === d.id) {
            d3.selectAll(".nodes circle").filter(function(n){ return n.id === sid || n.id === tid; })
                .classed("neighbor-node", true);
            d3.select("#link-" + sid + "-" + tid).classed("highlighted-link", true);
        }
    });
}

svg.on("click", function(){ clearClickHighlight(); });

function searchNode(){
    var term = document.getElementById("node-search").value.trim();
    clearClickHighlight();
    if (!term) return;
    var match = nodes.find(function(n){ return n.id.toUpperCase() === term.toUpperCase(); });
    var input = document.getElementById("node-search");
    if (match) {
        d3.select("#node-" + match.id).classed("clicked-node", true);
        input.classList.remove("search-not-found");
    } else {
        input.classList.add("search-not-found");
        setTimeout(function(){ input.classList.remove("search-not-found"); }, 600);
    }
}
document.getElementById("node-search").addEventListener("keypress", function(e){ if (e.keyCode === 13) searchNode(); });
document.getElementById("search-btn").addEventListener("click", searchNode);
document.getElementById("search-clear").addEventListener("click", function(){
    document.getElementById("node-search").value = ""; clearClickHighlight();
});

document.getElementById("label-toggle").addEventListener("change", function(){ labelsOn = this.checked; refreshVisibility(); });
document.getElementById("edge-toggle").addEventListener("change", function(){ edgesOn = this.checked; refreshVisibility(); });

function tiedSetsOf(info){
    // Older reports carried a single set; treat that as a one-element tie list.
    return (info && info.Ties && info.Ties.length) ? info.Ties : [info.KeySet];
}

function highlightSet(op, setIndex){
    d3.selectAll(".nodes circle").classed("keyplayer-node", false);
    currentKeySet = new Set();
    var info = keyInfoByOp.get(op);
    if (!info) return;
    var sets = tiedSetsOf(info);
    var chosen = sets[setIndex] || sets[0];
    chosen.forEach(function(id){ currentKeySet.add(id); });
    node.filter(function(d){ return currentKeySet.has(d.id); }).classed("keyplayer-node", true);
    document.getElementById("score-display").textContent = info.Score;
    document.getElementById("set-display").textContent = chosen.join(", ");
}

function applyKeyPlayerHighlight(op){
    var info = keyInfoByOp.get(op);
    var sets = tiedSetsOf(info);
    var total = (info && info.NOptimal) ? info.NOptimal : sets.length;
    var setSelect = document.getElementById("set-select");
    setSelect.innerHTML = "";
    sets.forEach(function(s, i){
        var o = document.createElement("option");
        o.value = String(i);
        o.textContent = "Set " + (i + 1) + ": " + s.join(", ");
        setSelect.appendChild(o);
    });
    // One optimum, nothing to choose between: the row stays out of the way.
    document.getElementById("tie-row").style.display = (sets.length > 1) ? "" : "none";
    document.getElementById("tie-note").textContent = (total > 1)
        ? (total > sets.length
            ? ("Showing " + sets.length + " of " + total + " sets that reach this score")
            : (total + " sets reach this score"))
        : "";
    highlightSet(op, 0);
}

var metricSelect = document.getElementById("metric-select");
metricSelect.addEventListener("change", function(){ applyKeyPlayerHighlight(this.value); });
document.getElementById("set-select").addEventListener("change", function(){
    highlightSet(metricSelect.value, parseInt(this.value, 10));
});
if (KEYINFO.length) { metricSelect.value = KEYINFO[0].Operation; applyKeyPlayerHighlight(KEYINFO[0].Operation); }

function buildVisibleClone(){
    var clone = d3.select(document.body).append("svg").attr("xmlns", "http://www.w3.org/2000/svg");

    clone.append("g").selectAll("line").data(links).enter().append("line")
        .attr("x1", function(d){ return d.source.x; }).attr("y1", function(d){ return d.source.y; })
        .attr("x2", function(d){ return d.target.x; }).attr("y2", function(d){ return d.target.y; })
        .attr("stroke", function(d){
            var live = d3.select("#link-" + linkEndpointId(d.source) + "-" + linkEndpointId(d.target));
            return live.classed("highlighted-link") ? "#de5246" : "#9aa5b1";
        })
        .attr("stroke-opacity", edgesOn ? 0.5 : 0).attr("stroke-width", 2);

    clone.append("g").selectAll("circle").data(nodes).enter().append("circle")
        .attr("r", NODE_RADIUS)
        .attr("cx", function(d){ return d.x; }).attr("cy", function(d){ return d.y; })
        .attr("fill", function(d){
            var live = d3.select("#node-" + d.id);
            if (live.classed("clicked-node")) return "#ffce44";
            if (live.classed("neighbor-node")) return "#de5246";
            if (currentKeySet.has(d.id)) return "#f44336";
            return "#3f7cac";
        });

    if (labelsOn) {
        clone.append("g").selectAll("text").data(nodes).enter().append("text")
            .text(function(d){ return d.id; })
            .attr("x", function(d){ return d.x + 8; }).attr("y", function(d){ return d.y + 3; });
    }

    var bbox = clone.node().getBBox();
    var margin = 40;
    clone.attr("viewBox", (bbox.x - margin / 2) + " " + (bbox.y - margin / 2) + " " + (bbox.width + margin) + " " + (bbox.height + margin))
         .attr("width", bbox.width + margin).attr("height", bbox.height + margin);
    return clone.node();
}

function triggerDownload(href, filename){
    var a = document.createElement("a");
    a.href = href; a.download = filename;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
}

function downloadSVG(){
    var clone = buildVisibleClone();
    var source = new XMLSerializer().serializeToString(clone);
    var blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
    triggerDownload(URL.createObjectURL(blob), DOWNLOAD_NAME);
    clone.remove();
}

function downloadPNG(){
    var clone = buildVisibleClone();
    var source = new XMLSerializer().serializeToString(clone);
    var url = URL.createObjectURL(new Blob([source], { type: "image/svg+xml;charset=utf-8" }));
    var img = new Image();
    img.onload = function(){
        var scale = 2; // rasterize at 2x for a crisper PNG than the on-screen SVG
        var canvas = document.createElement("canvas");
        canvas.width = img.width * scale; canvas.height = img.height * scale;
        var ctx = canvas.getContext("2d");
        ctx.fillStyle = "#ffffff"; ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.scale(scale, scale); ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(url);
        canvas.toBlob(function(pngBlob){
            triggerDownload(URL.createObjectURL(pngBlob), DOWNLOAD_NAME.replace(/\\.svg$/, ".png"));
        });
        clone.remove();
    };
    img.onerror = function(){ alert("PNG export failed while rasterizing the network snapshot."); clone.remove(); };
    img.src = url;
}

document.getElementById("export-svg-btn").addEventListener("click", downloadSVG);
document.getElementById("export-png-btn").addEventListener("click", downloadPNG);
})();
"""
        script_close = "\n</script>\n</body>\n</html>\n"
    else:
        script_open = ""
        script_body = ""
        script_close = "\n</body>\n</html>\n"

    final_string = body_top + script_open + script_body + script_close

    with open(outdir + "/" + filename + "_keyplayer.html", 'w') as f:
        f.write(final_string)





































#######################################################################################################################################################################
#######################################################################################################################################################################
#######################################################################################################################################################################
#######################################################################################################################################################################


# Rendering tiers for create_groupcentrality_html -- same rationale as the
# local/keyplayer reports: large graphs get a table-only fallback instead of
# an animated force layout the browser can't keep up with.
_GC_LIVE_MAX_NODES = 500
_GC_STATIC_MAX_NODES = 3000
_GC_STATIC_MAX_EDGES = 8000


def create_groupcentrality_html(df_metrics, grafo, outdir, filename):
    """Write the interactive group centrality report (<filename>_groupcentrality.html).

    df_metrics must have exactly the columns Operation/NodeSet/Score, one row
    per group-centrality metric (Degree/Betweenness/Closeness) -- NodeSet is a
    plain list of node names. Every algorithm in this codebase (brute force,
    greedy, gradient descent) returns exactly one optimal set per metric,
    never several candidates, so there is nothing to browse beyond picking
    the metric itself.

    The network is serialized as an edge list (O(E)), never a dense n x n
    adjacency matrix, mirroring the local-metrics/keyplayer reports' fix for
    the same memory/CPU wall.
    """
    n_nodes = grafo.vcount()
    n_edges = grafo.ecount()
    node_names = list(grafo.vs["name"])
    edges = grafo.get_edgelist()
    records = df_metrics.to_dict(orient="records")
    operations = [r["Operation"] for r in records]

    render_network = (n_nodes <= _GC_STATIC_MAX_NODES) and (n_edges <= _GC_STATIC_MAX_EDGES)
    live_animated = render_network and (n_nodes <= _GC_LIVE_MAX_NODES)

    # grafo.removed is None or a list of names; the old `str({grafo.removed})`
    # wrapped it in a Python set literal, which raised "unhashable type: list".
    info_items = (
        "<li>Removed nodes: " + str(grafo.removed) + "</li>"
        "<li>Number of components: " + str(len(grafo.components())) + "</li>"
        "<li>Number of Nodes: " + str(n_nodes) + "</li>"
        "<li>Number of Edges: " + str(n_edges) + "</li>"
    )

    name_output = str(filename) + ".svg"

    head = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Group Centrality Report</title>
    <script src="https://d3js.org/d3.v5.min.js"></script>
    <style>
:root{
  --bg:#f4f6f8; --surface:#ffffff; --border:#e0e4e8;
  --accent:#00796b; --accent-soft:#e0f2f1; --text:#1f2937; --text-soft:#5f6b7a;
  --radius:12px; --shadow:0 2px 8px rgba(15,23,42,.08);
}
*{box-sizing:border-box;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);}
.topbar{display:flex;align-items:center;gap:.75rem;padding:.75rem 1.25rem;background:var(--surface);border-bottom:1px solid var(--border);box-shadow:var(--shadow);}
.topbar img{height:36px;}
.topbar h1{font-size:1.05rem;margin:0;font-weight:600;color:var(--accent);}
.app-shell{display:grid;grid-template-columns:1fr 360px;gap:1rem;padding:1rem;align-items:start;}
@media (max-width:900px){.app-shell{grid-template-columns:1fr;}}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);padding:1rem;margin-bottom:1rem;}
.panel h2{font-size:.85rem;text-transform:uppercase;letter-spacing:.04em;color:var(--accent);margin:0 0 .75rem 0;font-weight:700;}
.graph-toolbar{display:flex;flex-wrap:wrap;gap:.9rem;align-items:center;padding:.25rem .25rem .75rem;}
svg#network{width:100%;height:70vh;background:var(--surface);border-radius:var(--radius);}
.btn-modern{border:none;border-radius:8px;padding:.4rem .9rem;font-size:.85rem;font-weight:600;background:var(--accent);color:#fff;cursor:pointer;transition:background .15s ease;}
.btn-modern:hover{background:#00695c;}
.field-row{display:flex;gap:.5rem;margin-bottom:.6rem;align-items:center;flex-wrap:wrap;}
input[type=text]{border:1px solid var(--border);border-radius:6px;padding:.35rem .5rem;font-size:.85rem;}
input.search-not-found{box-shadow:0 0 0 2px #de5246;}
select{border:1px solid var(--border);border-radius:6px;padding:.35rem .5rem;font-size:.85rem;}
.switch{position:relative;display:inline-block;width:34px;height:18px;}
.switch input{opacity:0;width:0;height:0;}
.slider-toggle{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background:#ccd3d9;transition:.2s;border-radius:34px;}
.slider-toggle:before{position:absolute;content:"";height:14px;width:14px;left:2px;bottom:2px;background:#fff;transition:.2s;border-radius:50%;}
input:checked+.slider-toggle{background:var(--accent);}
input:checked+.slider-toggle:before{transform:translateX(16px);}
.toggle-label{font-size:.82rem;color:var(--text-soft);margin-right:.3rem;}
ul.overview-list{list-style:none;margin:0;padding:0;font-size:.85rem;color:var(--text-soft);}
ul.overview-list li{padding:.15rem 0;}
.kp-readout{font-size:.85rem;color:var(--text-soft);}
.kp-readout b{color:var(--text);}
.kp-score{font-weight:700;color:var(--accent);}
.warning-banner{background:#fff8e1;border:1px solid #ffe082;color:#8d6e00;border-radius:var(--radius);padding:.85rem 1rem;margin-bottom:1rem;font-size:.9rem;}
.links line{stroke:#9aa5b1;stroke-opacity:.55;}
.nodes circle{stroke:#fff;stroke-width:1.2px;fill:#3f7cac;}
.nodetext text{font-size:11px;fill:var(--text);}
.hovered-node{fill:#ffce44 !important;}
.clicked-node{fill:#ffce44 !important;}
.neighbor-node{fill:#de5246 !important;}
.groupcentrality-node{fill:#f44336 !important;}
.highlighted-link{stroke:#de5246 !important;stroke-opacity:.5 !important;stroke-width:2px;}
table.metrics-table{width:100%;border-collapse:collapse;font-size:.82rem;}
table.metrics-table th,table.metrics-table td{padding:.4rem .5rem;border-bottom:1px solid var(--border);text-align:left;}
    </style>
</head>
<body>
<div class="topbar">
    <img src="https://camo.githubusercontent.com/21117091dc0315536e4ad1ccf7548c87c4626bc3563c1c96e3b40430114a3ae5/687474703a2f2f70796e7461636c652e6373732d6d656e64656c2e69742f696d616765732f7469746c655f6a6f696e65642e706e67">
    <h1>Group Centrality Report &mdash; """ + html.escape(str(filename)) + """</h1>
</div>
<div class="app-shell">
<div>
"""

    sidebar_overview = """
<div class="panel">
    <h2>Network Overview</h2>
    <ul class="overview-list">""" + info_items + """</ul>
</div>
"""

    if render_network:
        warning_html = ""
        main_panel = """
<div class="panel">
    <div class="graph-toolbar">
        <button id="export-svg-btn" class="btn-modern">Export SVG</button>
        <button id="export-png-btn" class="btn-modern">Export PNG</button>
        <span class="toggle-label">Node labels</span>
        <label class="switch"><input type="checkbox" id="label-toggle"><span class="slider-toggle"></span></label>
        <span class="toggle-label">Edges</span>
        <label class="switch"><input type="checkbox" id="edge-toggle" checked><span class="slider-toggle"></span></label>
    </div>
    <div id="box-to-export">
        <svg id="network" viewBox="0 0 1200 700" preserveAspectRatio="xMidYMid meet"></svg>
    </div>
</div>
"""
        sidebar_controls = """
<div class="panel">
    <h2>Search</h2>
    <div class="field-row">
        <input type="text" id="node-search" placeholder="Node name">
        <button id="search-btn" class="btn-modern">Find</button>
        <button id="search-clear" class="btn-modern" style="background:var(--accent-soft);color:var(--accent);">Clear</button>
    </div>
</div>
<div class="panel">
    <h2>Group centrality metric</h2>
    <div class="field-row">
        <select id="metric-select">""" + "".join(
            '<option value="{0}">{0}</option>'.format(html.escape(str(op))) for op in operations
        ) + """</select>
    </div>
    <div class="field-row" id="tie-row" style="display:none;">
        <select id="set-select"></select>
    </div>
    <p class="kp-readout" id="tie-note"></p>
    <p class="kp-readout">Score: <span id="score-display" class="kp-score">--</span></p>
    <p class="kp-readout"><b>Group centrality set:</b> <span id="set-display">--</span></p>
</div>
"""
        table_html = ""
    else:
        warning_html = (
            '<div class="warning-banner">This network has ' + str(n_nodes) + ' nodes and '
            + str(n_edges) + ' edges, above the practical limit for a smooth interactive layout '
            '(' + str(_GC_STATIC_MAX_NODES) + ' nodes / ' + str(_GC_STATIC_MAX_EDGES) + ' edges). '
            'Showing the group centrality sets as a table only &mdash; no network view was built.</div>'
        )
        rows_html = "".join(
            "<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>".format(
                html.escape(str(r["Operation"])),
                html.escape(str(r["Score"])),
                html.escape(", ".join(str(x) for x in r["NodeSet"])),
            ) for r in records
        )
        main_panel = """
<div class="panel">
    <h2>Group centrality sets</h2>
    <div style="overflow-x:auto;">
    <table class="metrics-table">
        <thead><tr><th>Operation</th><th>Score</th><th>Node set</th></tr></thead>
        <tbody>""" + rows_html + """</tbody>
    </table>
    </div>
</div>
"""
        sidebar_controls = ""
        table_html = ""

    body_top = (
        head + warning_html + main_panel + "</div><div>" + sidebar_overview
        + sidebar_controls + "</div></div>" + table_html
    )

    if render_network:
        script_open = "\n<script>\n"
        script_body = """
(function(){
var NODE_NAMES = """ + json.dumps(node_names) + """;
var EDGES = """ + json.dumps(edges) + """;
var GCINFO = """ + json.dumps(records) + """;
var LIVE_ANIMATED = """ + ("true" if live_animated else "false") + """;
var DOWNLOAD_NAME = """ + json.dumps(name_output) + """;

var gcInfoByOp = new Map(GCINFO.map(function(d){ return [d.Operation, d]; }));

var nodes = NODE_NAMES.map(function(name){ return { id: name }; });
var links = EDGES.map(function(e){ return { source: nodes[e[0]].id, target: nodes[e[1]].id }; });

var NODE_RADIUS = 6;

var svg = d3.select("#network");
var viewBoxParts = svg.attr("viewBox").split(" ").map(Number);
var width = viewBoxParts[2], height = viewBoxParts[3];

var g = svg.append("g");
svg.call(d3.zoom().scaleExtent([0.2, 12]).on("zoom", function(){ g.attr("transform", d3.event.transform); }));

var link = g.append("g").attr("class", "links").selectAll("line")
    .data(links).enter().append("line")
    .attr("id", function(d){ return "link-" + d.source + "-" + d.target; });

var node = g.append("g").attr("class", "nodes").selectAll("circle")
    .data(nodes).enter().append("circle")
    .attr("r", NODE_RADIUS)
    .attr("id", function(d){ return "node-" + d.id; })
    .on("click", showNodeInfo)
    .call(d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended));

var labels = g.append("g").attr("class", "nodetext").selectAll("text")
    .data(nodes).enter().append("text")
    .text(function(d){ return d.id; })
    .style("visibility", "hidden");

var labelsOn = false, edgesOn = true, highlightedNode = null, currentNodeSet = new Set();

function linkEndpointId(x){ return (x && typeof x === "object") ? x.id : x; }

function refreshVisibility(){
    link.style("display", function(){ return edgesOn ? null : "none"; });
    labels.style("visibility", function(){ return labelsOn ? "visible" : "hidden"; });
}

var simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(function(d){ return d.id; }).distance(40))
    .force("charge", d3.forceManyBody().strength(-60))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide(8));

function ticked(){
    link.attr("x1", function(d){ return d.source.x; }).attr("y1", function(d){ return d.source.y; })
        .attr("x2", function(d){ return d.target.x; }).attr("y2", function(d){ return d.target.y; });
    node.attr("cx", function(d){ return d.x; }).attr("cy", function(d){ return d.y; });
    labels.attr("x", function(d){ return d.x + 8; }).attr("y", function(d){ return d.y + 3; });
}

if (LIVE_ANIMATED) {
    simulation.on("tick", ticked);
} else {
    // Medium graphs: settle the layout once, synchronously, instead of
    // paying for a physics loop the tab would have to keep alive forever.
    simulation.stop();
    var settleTicks = Math.min(300, Math.ceil(Math.log(nodes.length + 1) * 60));
    for (var i = 0; i < settleTicks; i++) simulation.tick();
    ticked();
}
refreshVisibility();

function dragstarted(d){
    if (LIVE_ANIMATED && !d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x; d.fy = d.y;
}
function dragged(d){
    d.fx = d3.event.x; d.fy = d3.event.y;
    if (!LIVE_ANIMATED) { d.x = d.fx; d.y = d.fy; ticked(); }
}
function dragended(d){
    if (LIVE_ANIMATED && !d3.event.active) simulation.alphaTarget(0);
    d.fx = null; d.fy = null;
}

node.on("mouseover", function(d){
    d3.select(this).classed("hovered-node", true);
    labels.filter(function(l){ return l.id === d.id; }).style("visibility", "visible");
}).on("mouseout", function(d){
    if (highlightedNode === d.id) return;
    d3.select(this).classed("hovered-node", false);
    labels.filter(function(l){ return l.id === d.id; })
        .style("visibility", labelsOn ? "visible" : "hidden");
});

function clearClickHighlight(){
    // .hovered-node can be left set by mouseout's early-return above while a
    // node is the active selection -- must be cleared here too, or the
    // yellow fill sticks around after the mouse has long since left.
    d3.selectAll(".nodes circle").classed("clicked-node", false).classed("neighbor-node", false).classed("hovered-node", false);
    d3.selectAll(".links line").classed("highlighted-link", false);
    highlightedNode = null;
}

function showNodeInfo(d){
    d3.event.stopPropagation();
    clearClickHighlight();
    d3.select(this).classed("clicked-node", true);
    highlightedNode = d.id;

    links.forEach(function(l){
        var sid = linkEndpointId(l.source), tid = linkEndpointId(l.target);
        if (sid === d.id || tid === d.id) {
            d3.selectAll(".nodes circle").filter(function(n){ return n.id === sid || n.id === tid; })
                .classed("neighbor-node", true);
            d3.select("#link-" + sid + "-" + tid).classed("highlighted-link", true);
        }
    });
}

svg.on("click", function(){ clearClickHighlight(); });

function searchNode(){
    var term = document.getElementById("node-search").value.trim();
    clearClickHighlight();
    if (!term) return;
    var match = nodes.find(function(n){ return n.id.toUpperCase() === term.toUpperCase(); });
    var input = document.getElementById("node-search");
    if (match) {
        d3.select("#node-" + match.id).classed("clicked-node", true);
        input.classList.remove("search-not-found");
    } else {
        input.classList.add("search-not-found");
        setTimeout(function(){ input.classList.remove("search-not-found"); }, 600);
    }
}
document.getElementById("node-search").addEventListener("keypress", function(e){ if (e.keyCode === 13) searchNode(); });
document.getElementById("search-btn").addEventListener("click", searchNode);
document.getElementById("search-clear").addEventListener("click", function(){
    document.getElementById("node-search").value = ""; clearClickHighlight();
});

document.getElementById("label-toggle").addEventListener("change", function(){ labelsOn = this.checked; refreshVisibility(); });
document.getElementById("edge-toggle").addEventListener("change", function(){ edgesOn = this.checked; refreshVisibility(); });

function tiedSetsOf(info){
    // Older reports carried a single set; treat that as a one-element tie list.
    return (info && info.Ties && info.Ties.length) ? info.Ties : [info.NodeSet];
}

function highlightSet(op, setIndex){
    d3.selectAll(".nodes circle").classed("groupcentrality-node", false);
    currentNodeSet = new Set();
    var info = gcInfoByOp.get(op);
    if (!info) return;
    var sets = tiedSetsOf(info);
    var chosen = sets[setIndex] || sets[0];
    chosen.forEach(function(id){ currentNodeSet.add(id); });
    node.filter(function(d){ return currentNodeSet.has(d.id); }).classed("groupcentrality-node", true);
    document.getElementById("score-display").textContent = info.Score;
    document.getElementById("set-display").textContent = chosen.join(", ");
}

function applyGroupCentralityHighlight(op){
    var info = gcInfoByOp.get(op);
    var sets = tiedSetsOf(info);
    var total = (info && info.NOptimal) ? info.NOptimal : sets.length;
    var setSelect = document.getElementById("set-select");
    setSelect.innerHTML = "";
    sets.forEach(function(s, i){
        var o = document.createElement("option");
        o.value = String(i);
        o.textContent = "Set " + (i + 1) + ": " + s.join(", ");
        setSelect.appendChild(o);
    });
    // One optimum, nothing to choose between: the row stays out of the way.
    document.getElementById("tie-row").style.display = (sets.length > 1) ? "" : "none";
    document.getElementById("tie-note").textContent = (total > 1)
        ? (total > sets.length
            ? ("Showing " + sets.length + " of " + total + " sets that reach this score")
            : (total + " sets reach this score"))
        : "";
    highlightSet(op, 0);
}

var metricSelect = document.getElementById("metric-select");
metricSelect.addEventListener("change", function(){ applyGroupCentralityHighlight(this.value); });
document.getElementById("set-select").addEventListener("change", function(){
    highlightSet(metricSelect.value, parseInt(this.value, 10));
});
if (GCINFO.length) { metricSelect.value = GCINFO[0].Operation; applyGroupCentralityHighlight(GCINFO[0].Operation); }

function buildVisibleClone(){
    var clone = d3.select(document.body).append("svg").attr("xmlns", "http://www.w3.org/2000/svg");

    clone.append("g").selectAll("line").data(links).enter().append("line")
        .attr("x1", function(d){ return d.source.x; }).attr("y1", function(d){ return d.source.y; })
        .attr("x2", function(d){ return d.target.x; }).attr("y2", function(d){ return d.target.y; })
        .attr("stroke", function(d){
            var live = d3.select("#link-" + linkEndpointId(d.source) + "-" + linkEndpointId(d.target));
            return live.classed("highlighted-link") ? "#de5246" : "#9aa5b1";
        })
        .attr("stroke-opacity", edgesOn ? 0.5 : 0).attr("stroke-width", 2);

    clone.append("g").selectAll("circle").data(nodes).enter().append("circle")
        .attr("r", NODE_RADIUS)
        .attr("cx", function(d){ return d.x; }).attr("cy", function(d){ return d.y; })
        .attr("fill", function(d){
            var live = d3.select("#node-" + d.id);
            if (live.classed("clicked-node")) return "#ffce44";
            if (live.classed("neighbor-node")) return "#de5246";
            if (currentNodeSet.has(d.id)) return "#f44336";
            return "#3f7cac";
        });

    if (labelsOn) {
        clone.append("g").selectAll("text").data(nodes).enter().append("text")
            .text(function(d){ return d.id; })
            .attr("x", function(d){ return d.x + 8; }).attr("y", function(d){ return d.y + 3; });
    }

    var bbox = clone.node().getBBox();
    var margin = 40;
    clone.attr("viewBox", (bbox.x - margin / 2) + " " + (bbox.y - margin / 2) + " " + (bbox.width + margin) + " " + (bbox.height + margin))
         .attr("width", bbox.width + margin).attr("height", bbox.height + margin);
    return clone.node();
}

function triggerDownload(href, filename){
    var a = document.createElement("a");
    a.href = href; a.download = filename;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
}

function downloadSVG(){
    var clone = buildVisibleClone();
    var source = new XMLSerializer().serializeToString(clone);
    var blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
    triggerDownload(URL.createObjectURL(blob), DOWNLOAD_NAME);
    clone.remove();
}

function downloadPNG(){
    var clone = buildVisibleClone();
    var source = new XMLSerializer().serializeToString(clone);
    var url = URL.createObjectURL(new Blob([source], { type: "image/svg+xml;charset=utf-8" }));
    var img = new Image();
    img.onload = function(){
        var scale = 2; // rasterize at 2x for a crisper PNG than the on-screen SVG
        var canvas = document.createElement("canvas");
        canvas.width = img.width * scale; canvas.height = img.height * scale;
        var ctx = canvas.getContext("2d");
        ctx.fillStyle = "#ffffff"; ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.scale(scale, scale); ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(url);
        canvas.toBlob(function(pngBlob){
            triggerDownload(URL.createObjectURL(pngBlob), DOWNLOAD_NAME.replace(/\\.svg$/, ".png"));
        });
        clone.remove();
    };
    img.onerror = function(){ alert("PNG export failed while rasterizing the network snapshot."); clone.remove(); };
    img.src = url;
}

document.getElementById("export-svg-btn").addEventListener("click", downloadSVG);
document.getElementById("export-png-btn").addEventListener("click", downloadPNG);
})();
"""
        script_close = "\n</script>\n</body>\n</html>\n"
    else:
        script_open = ""
        script_body = ""
        script_close = "\n</body>\n</html>\n"

    final_string = body_top + script_open + script_body + script_close

    with open(outdir + "/" + filename + "_groupcentrality.html", 'w') as f:
        f.write(final_string)
