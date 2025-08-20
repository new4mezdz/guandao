# 完整版增强 test2.py - 修复所有语法错误并解决节点悬停跳动问题
import sqlite3
import json
import os


def generate_fixed_interactive_html():
    """生成修复版交互式HTML可视化"""
    print("🎨 正在生成完整版交互式可视化...")

    # 读取数据库数据
    conn = sqlite3.connect("my_database.db")
    c = conn.cursor()

    # 读取节点
    c.execute("SELECT Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y FROM building_nodes")
    nodes_data = c.fetchall()

    # 读取管道
    c.execute("SELECT Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status FROM pipes")
    pipes_data = c.fetchall()

    # 读取阀门
    c.execute("SELECT Valve_ID, Controlled_Pipe_ID, Status FROM valves")
    valves_data = c.fetchall()

    conn.close()

    if not nodes_data or not pipes_data:
        print("❌ 数据库中没有数据，请先运行 create.py")
        return False

    # 转换数据格式
    nodes = []
    color_map = {'A': '#ff4444', 'B': '#ff8800', 'C': '#44ff44'}

    for node in nodes_data:
        nodes.append({
            'id': node[0],
            'name': node[1],
            'type': node[2],
            'level': node[3],
            'original_x': float(node[4]),
            'original_y': float(node[5]),
            'color': color_map.get(node[3], '#cccccc')
        })

    links = []
    for pipe in pipes_data:
        links.append({
            'id': pipe[0],
            'source': pipe[1],
            'target': pipe[2],
            'diameter': pipe[3],
            'status': pipe[4]
        })

    valves = {v[1]: {'id': v[0], 'status': v[2]} for v in valves_data}

    # 将数据转换为JSON字符串
    nodes_json = json.dumps(nodes, ensure_ascii=False)
    links_json = json.dumps(links, ensure_ascii=False)
    valves_json = json.dumps(valves, ensure_ascii=False)

    # 创建HTML内容 - 分段创建避免语法错误
    html_start = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>供水网络交互式可视化 - 完整增强版</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(45deg, #2196F3, #21CBF3);
            color: white;
            padding: 20px;
            text-align: center;
        }

        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 300;
        }

        .controls {
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }

        .control-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        select, input, button {
            padding: 10px 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
        }

        button {
            background: linear-gradient(45deg, #007bff, #0056b3);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 500;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,123,255,0.3);
        }

        .main-content {
            display: flex;
            height: 700px;
        }

        .viz-container {
            flex: 1;
            position: relative;
            overflow: hidden;
            background: #fafafa;
        }

        .info-panel {
            width: 350px;
            background: white;
            border-left: 1px solid #e9ecef;
            padding: 20px;
            overflow-y: auto;
        }

        svg {
            width: 100%;
            height: 100%;
            cursor: grab;
        }

        svg:active {
            cursor: grabbing;
        }

        .node {
            stroke: #fff;
            stroke-width: 3px;
            cursor: pointer;
            transition: all 0.3s;
            filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.2));
        }

        .node:hover {
            stroke-width: 4px;
        }

        .node.selected {
            stroke: #00ff00;
            stroke-width: 5px;
            filter: drop-shadow(0 0 15px #00ff00);
            animation: glow 2s infinite alternate;
        }

        .node.leak {
            stroke: #ff0000;
            stroke-width: 5px;
            filter: drop-shadow(0 0 10px #ff0000);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }

        @keyframes glow {
            0% { filter: drop-shadow(0 0 10px #00ff00); }
            100% { filter: drop-shadow(0 0 20px #00ff00); }
        }

        .link {
            stroke: #999;
            stroke-opacity: 0.8;
            stroke-width: 3px;
            fill: none;
            transition: all 0.3s;
            cursor: pointer;
        }

        .link:hover {
            stroke-width: 5px;
            stroke-opacity: 1;
        }

        .link.highlighted {
            stroke: #ff4444;
            stroke-width: 6px;
            stroke-opacity: 1;
            filter: drop-shadow(0 0 8px #ff4444);
            animation: flow 1s infinite linear;
        }

        .link.selected {
            stroke: #007bff;
            stroke-width: 8px;
            stroke-opacity: 1;
            filter: drop-shadow(0 0 10px #007bff);
        }

        @keyframes flow {
            0% { stroke-dashoffset: 0; }
            100% { stroke-dashoffset: 20; }
        }

        .arrow {
            fill: #666;
            transition: all 0.3s;
        }

        .arrow.highlighted {
            fill: #ff4444;
        }

        .node-label {
            font-size: 12px;
            font-weight: bold;
            text-anchor: middle;
            pointer-events: none;
            fill: #333;
            text-shadow: 1px 1px 2px white;
        }

        .legend {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255,255,255,0.95);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            min-width: 150px;
        }

        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            font-size: 13px;
        }

        .legend-color {
            width: 18px;
            height: 18px;
            border-radius: 50%;
            margin-right: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }

        .status {
            padding: 15px 20px;
            text-align: center;
            background: linear-gradient(45deg, #e9ecef, #f8f9fa);
            font-size: 14px;
            font-weight: 500;
        }

        .info-section {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }

        .coordinate-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 12px;
        }

        .coordinate-table th,
        .coordinate-table td {
            border: 1px solid #ddd;
            padding: 6px 8px;
            text-align: left;
        }

        .coordinate-table th {
            background: #e9ecef;
            font-weight: bold;
        }

        .result-panel {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
        }

        .clear-btn, .test-btn {
            background: #28a745;
            font-size: 12px;
            padding: 5px 10px;
            margin: 5px 5px 0 0;
        }

        .test-btn {
            background: #17a2b8;
        }

        .valve-info {
            background: #e8f4fd;
            border: 1px solid #bee5eb;
            border-radius: 8px;
            padding: 10px;
            margin-top: 10px;
        }

        .valve-status {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        }

        .valve-status.normal {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .valve-status.failed {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚰 供水网络交互式可视化系统</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">节点: """ + str(len(nodes)) + """ | 管道: """ + str(
        len(links)) + """ | 阀门: """ + str(len(valves)) + """ | ✨ 功能：节点坐标与管道阀门显示</p>
        </div>

        <div class="controls">
            <div class="control-group">
                <label><strong>漏损类型:</strong></label>
                <select id="leakType" onchange="onLeakTypeChange()">
                    <option value="节点漏损">1. 节点漏损</option>
                    <option value="管道漏损">2. 管道漏损</option>
                    <option value="爆管">3. 爆管</option>
                </select>
            </div>

            <div class="control-group" id="nodeInputGroup">
                <label><strong>漏损节点:</strong></label>
                <input type="text" id="leakNode" placeholder="如: N001">
            </div>

            <div class="control-group" id="pipeInputGroup" style="display: none;">
                <label><strong>漏损管道:</strong></label>
                <input type="text" id="leakPipe" placeholder="如: P0001">
            </div>

            <div class="control-group">
                <label><strong>失效阀门:</strong></label>
                <input type="text" id="failValve" placeholder="如: V0001 (可选)">
            </div>

            <button onclick="performRealIsolation()">🔍 执行隔离分析</button>
            <button onclick="resetVisualization()">🔄 重置视图</button>
            <button onclick="showAllPipes()">👁️ 显示所有管道</button>
            <button onclick="clearAllSelections()">🧹 清除选择</button>
        </div>

        <div class="main-content">
            <div class="viz-container">
                <svg id="networkSvg"></svg>

                <div class="legend">
                    <h4 style="margin-top: 0;">图例</h4>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #ff4444;"></div>
                        <span>A级 水厂</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #ff8800;"></div>
                        <span>B级 学校</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #44ff44;"></div>
                        <span>C级 住宅</span>
                    </div>
                    <hr style="margin: 15px 0;">
                    <div class="legend-item">
                        <div style="width: 20px; height: 4px; background: #ff4444; margin-right: 8px; border-radius: 2px;"></div>
                        <span>需关闭管道</span>
                    </div>
                    <div class="legend-item">
                        <div style="width: 16px; height: 16px; background: #00ff00; margin-right: 10px; border-radius: 50%; box-shadow: 0 0 8px #00ff00;"></div>
                        <span>已选择节点</span>
                    </div>
                    <div class="legend-item">
                        <div style="width: 20px; height: 4px; background: #007bff; margin-right: 8px; border-radius: 2px; box-shadow: 0 0 6px #007bff;"></div>
                        <span>已选择管道</span>
                    </div>
                </div>
            </div>

            <div class="info-panel">
                <div class="info-section" id="nodeInfo">
                    <h4 style="margin-top: 0;">节点信息</h4>
                    <p>👆 点击左侧网络图中的任意节点查看详细信息</p>
                </div>

                <div class="info-section" id="pipeInfo" style="display: none;">
                    <h4 style="margin-top: 0;">🔧 管道信息</h4>
                    <div id="pipeDetails"></div>
                </div>

                <div class="info-section" id="coordinateInfo" style="display: none;">
                    <h4 style="margin-top: 0;">📍 坐标信息</h4>
                    <table class="coordinate-table">
                        <tr>
                            <th>坐标类型</th>
                            <th>X 坐标</th>
                            <th>Y 坐标</th>
                        </tr>
                        <tr>
                            <td>数据库原始</td>
                            <td id="dbX">-</td>
                            <td id="dbY">-</td>
                        </tr>
                        <tr>
                            <td>D3 计算坐标</td>
                            <td id="d3X">-</td>
                            <td id="d3Y">-</td>
                        </tr>
                        <tr>
                            <td>当前屏幕坐标</td>
                            <td id="screenX">-</td>
                            <td id="screenY">-</td>
                        </tr>
                    </table>
                    <button class="clear-btn" onclick="clearNodeSelection()">清除选择</button>
                    <button class="test-btn" onclick="testCoordinates()">测试坐标</button>
                </div>

                <div class="info-section" id="isolationResult" style="display: none;">
                    <h4 style="margin-top: 0; color: #d63384;">隔离结果</h4>
                    <div id="resultContent"></div>
                </div>
            </div>
        </div>

        <div class="status" id="status">
            ✅ 系统已加载 - 点击节点查看坐标信息，点击管道查看阀门信息
        </div>
    </div>

    <script>"""

    # JavaScript部分
    js_content = """
        // 数据
        const nodesData = """ + nodes_json + """;
        const linksData = """ + links_json + """;
        const valvesData = """ + valves_json + """;

        // 全局变量
        let nodes = [];
        let links = [];
        let simulation;
        let svg, g;
        let highlightedLinks = new Set();
        let currentIsolationResult = null;
        let selectedNode = null;
        let selectedPipe = null;

        console.log('加载数据:', nodesData.length, '个节点,', linksData.length, '条管道');

        // 初始化
        function init() {
            nodes = nodesData.map(d => ({...d}));
            links = linksData.map(d => ({
                ...d,
                source: d.source,
                target: d.target
            }));

            svg = d3.select("#networkSvg");
            g = svg.append("g");

            const zoom = d3.zoom()
                .scaleExtent([0.1, 4])
                .on("zoom", (event) => {
                    g.attr("transform", event.transform);
                    updateCurrentCoordinates();
                });

            svg.call(zoom);
            updateVisualization();
        }

        // 更新可视化
        function updateVisualization() {
            const width = parseInt(svg.style("width")) || 800;
            const height = parseInt(svg.style("height")) || 600;

            g.selectAll("*").remove();

            svg.select("defs").remove();
            svg.append("defs").selectAll("marker")
                .data(["normal", "highlighted"])
                .enter().append("marker")
                .attr("id", d => "arrow-" + d)
                .attr("viewBox", "0 -5 10 10")
                .attr("refX", 20)
                .attr("refY", 0)
                .attr("markerWidth", 6)
                .attr("markerHeight", 6)
                .attr("orient", "auto")
                .append("path")
                .attr("d", "M0,-5L10,0L0,5")
                .attr("class", "arrow")
                .style("fill", d => d === "highlighted" ? "#ff4444" : "#666");

            // 绘制连接
            const link = g.append("g")
                .selectAll("line")
                .data(links)
                .enter().append("line")
                .attr("class", "link")
                .attr("id", d => "link-" + d.id)
                .attr("marker-end", "url(#arrow-normal)")
                .attr("stroke-width", d => Math.max(2, d.diameter / 100))
                .on("mouseover", function(event, d) {
                    var valve = valvesData[d.id];
                    var content = "管道: " + d.id + "<br>" +
                                "直径: " + d.diameter + "mm<br>" +
                                "状态: " + d.status + "<br>" +
                                (valve ? "阀门: " + valve.id + " (" + valve.status + ")" : "无阀门");
                    showTooltip(event, content);
                })
                .on("mouseout", function() {
                    hideTooltip();
                })
                .on("click", function(event, d) {
                    event.stopPropagation();
                    console.log('管道被点击:', d);

                    var leakType = document.getElementById("leakType").value;
                    if (leakType === "管道漏损" || leakType === "爆管") {
                        document.getElementById("leakPipe").value = d.id;
                    } else {
                        var sourceId = d.source.id || d.source;
                        document.getElementById("leakNode").value = sourceId;
                    }

                    selectPipe(d);
                });

            // 绘制节点
            const node = g.append("g")
                .selectAll("circle")
                .data(nodes)
                .enter().append("circle")
                .attr("class", "node")
                .attr("r", d => d.level === 'A' ? 12 : (d.level === 'B' ? 10 : 8))
                .attr("fill", d => d.color)
                .on("click", function(event, d) {
                    event.stopPropagation();
                    console.log('节点被点击:', d);
                    selectNodeFunction(d);
                })
                .on("mouseover", function(event, d) {
                    // 平滑地将半径放大 1.5 倍
                    const originalRadius = d.level === 'A' ? 12 : (d.level === 'B' ? 10 : 8);
                    d3.select(this).transition()
                        .duration(200) // 动画时长200毫秒
                        .attr("r", originalRadius * 1.5);
                })
                .on("mouseout", function(event, d) {
                    // 平滑地恢复原始半径
                    const originalRadius = d.level === 'A' ? 12 : (d.level === 'B' ? 10 : 8);
                    d3.select(this).transition()
                        .duration(200)
                        .attr("r", originalRadius);
                })
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));

            // 添加节点标签
            const labels = g.append("g")
                .selectAll("text")
                .data(nodes)
                .enter().append("text")
                .attr("class", "node-label")
                .text(d => d.id)
                .attr("dy", d => d.level === 'A' ? 16 : (d.level === 'B' ? 14 : 12));

            // 创建力导向图模拟
            simulation = d3.forceSimulation(nodes)
                .force("link", d3.forceLink(links)
                    .id(d => d.id)
                    .distance(d => Math.min(150, Math.max(50, d.diameter / 2)))
                )
                .force("charge", d3.forceManyBody().strength(-500))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("collision", d3.forceCollide().radius(d => (d.level === 'A' ? 20 : 15)));

            simulation.on("tick", () => {
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);

                node
                    .attr("cx", d => d.x)
                    .attr("cy", d => d.y);

                labels
                    .attr("x", d => d.x)
                    .attr("y", d => d.y);

                updateCurrentCoordinates();
            });
        }

        // 选择节点功能
        function selectNodeFunction(node) {
            console.log('选择节点:', node);
            selectedNode = node;

            selectedPipe = null;
            d3.selectAll(".link").classed("selected", false);
            document.getElementById("pipeInfo").style.display = "none";

            d3.selectAll(".node")
                .classed("selected", function(d) { return d.id === node.id; });

            document.getElementById("nodeInfo").innerHTML = 
                "<h4 style='margin-top: 0;'>节点详情</h4>" +
                "<p><strong>" + node.name + "</strong></p>" +
                "<p>ID: " + node.id + "</p>" +
                "<p>等级: " + node.level + "</p>" +
                "<p>类型: " + node.type + "</p>";

            document.getElementById("coordinateInfo").style.display = "block";
            updateCoordinateDisplay();
            document.getElementById("leakNode").value = node.id;
            updateStatus("✅ 已选择节点: " + node.id + " - " + node.name);
        }

        // 选择管道功能
        function selectPipe(pipe) {
            console.log('选择管道:', pipe);
            selectedPipe = pipe;

            selectedNode = null;
            d3.selectAll(".node").classed("selected", false);
            document.getElementById("coordinateInfo").style.display = "none";

            d3.selectAll(".link")
                .classed("selected", function(d) { return d.id === pipe.id; });

            showPipeInfo(pipe);
            updateStatus("🔧 已选择管道: " + pipe.id + " (点击其他管道或节点切换选择)");
        }

        // 显示管道信息
        function showPipeInfo(pipe) {
            var sourceId = pipe.source.id || pipe.source;
            var targetId = pipe.target.id || pipe.target;
            var sourceNode = nodes.find(function(n) { return n.id === sourceId; });
            var targetNode = nodes.find(function(n) { return n.id === targetId; });
            var valve = valvesData[pipe.id];

            var pipeHtml = 
                "<p><strong>管道ID:</strong> " + pipe.id + "</p>" +
                "<p><strong>直径:</strong> " + pipe.diameter + " mm</p>" +
                "<p><strong>状态:</strong> " + pipe.status + "</p>" +
                "<p><strong>起始节点:</strong> " + sourceId + 
                (sourceNode ? " (" + sourceNode.name + ")" : "") + "</p>" +
                "<p><strong>终端节点:</strong> " + targetId + 
                (targetNode ? " (" + targetNode.name + ")" : "") + "</p>";

            if (valve) {
                var statusClass = valve.status === "正常" ? "normal" : "failed";
                pipeHtml += 
                    "<div class='valve-info'>" +
                    "<h5 style='margin: 0 0 10px 0;'>🔧 控制阀门</h5>" +
                    "<p><strong>阀门ID:</strong> " + valve.id + "</p>" +
                    "<p><strong>状态:</strong> <span class='valve-status " + statusClass + "'>" + valve.status + "</span></p>" +
                    "<p style='font-size: 12px; color: #666; margin: 10px 0 0 0;'>" +
                    "💡 " + (valve.status === "正常" ? "阀门工作正常，可用于隔离控制" : "阀门故障，无法用于隔离控制") +
                    "</p>" +
                    "</div>";
            } else {
                pipeHtml += 
                    "<div class='valve-info'>" +
                    "<h5 style='margin: 0 0 10px 0;'>⚠️ 阀门信息</h5>" +
                    "<p style='color: #dc3545;'>此管道没有控制阀门</p>" +
                    "<p style='font-size: 12px; color: #666; margin: 10px 0 0 0;'>" +
                    "💡 无阀门管道需要通过其他方式进行隔离" +
                    "</p>" +
                    "</div>";
            }

            pipeHtml += 
                "<button class='clear-btn' onclick='clearPipeSelection()' style='margin-top: 10px;'>清除选择</button>" +
                "<button class='test-btn' onclick='highlightPipeConnections()' style='margin-top: 10px;'>显示连接</button>";

            document.getElementById("pipeInfo").style.display = "block";
            document.getElementById("pipeDetails").innerHTML = pipeHtml;

            document.getElementById("nodeInfo").innerHTML = 
                "<h4 style='margin-top: 0;'>节点信息</h4>" +
                "<p>👆 点击左侧网络图中的任意节点查看详细信息</p>";
        }

        // 其他功能函数
        function clearPipeSelection() {
            selectedPipe = null;
            d3.selectAll(".link").classed("selected", false);
            document.getElementById("pipeInfo").style.display = "none";
            updateStatus("🔄 已清除管道选择 - 点击管道或节点查看信息");
        }

        function highlightPipeConnections() {
            if (!selectedPipe) {
                alert("请先选择一个管道");
                return;
            }

            var sourceId = selectedPipe.source.id || selectedPipe.source;
            var targetId = selectedPipe.target.id || selectedPipe.target;

            d3.selectAll(".node")
                .classed("leak", function(d) { 
                    return d.id === sourceId || d.id === targetId; 
                });

            highlightedLinks.clear();
            highlightedLinks.add(selectedPipe.id);
            updateLinkHighlights();

            updateStatus("🎯 已高亮管道 " + selectedPipe.id + " 的连接节点: " + sourceId + " ↔ " + targetId);
        }

        function showTooltip(event, content) {
            var tooltip = document.createElement('div');
            tooltip.innerHTML = content;
            tooltip.style.position = 'absolute';
            tooltip.style.background = 'rgba(0,0,0,0.8)';
            tooltip.style.color = 'white';
            tooltip.style.padding = '8px';
            tooltip.style.borderRadius = '4px';
            tooltip.style.fontSize = '12px';
            tooltip.style.pointerEvents = 'none';
            tooltip.style.zIndex = '1000';
            tooltip.style.left = (event.pageX + 10) + 'px';
            tooltip.style.top = (event.pageY - 10) + 'px';
            tooltip.id = 'temp-tooltip';

            var existingTooltip = document.getElementById('temp-tooltip');
            if (existingTooltip) {
                existingTooltip.remove();
            }

            document.body.appendChild(tooltip);
        }

        function hideTooltip() {
            var tooltip = document.getElementById('temp-tooltip');
            if (tooltip) {
                tooltip.remove();
            }
        }

        function updateCoordinateDisplay() {
            if (!selectedNode) return;

            var dbXEl = document.getElementById("dbX");
            var dbYEl = document.getElementById("dbY");
            var d3XEl = document.getElementById("d3X");
            var d3YEl = document.getElementById("d3Y");

            if (dbXEl) dbXEl.textContent = selectedNode.original_x.toFixed(4);
            if (dbYEl) dbYEl.textContent = selectedNode.original_y.toFixed(4);
            if (d3XEl) d3XEl.textContent = (selectedNode.x || 0).toFixed(2);
            if (d3YEl) d3YEl.textContent = (selectedNode.y || 0).toFixed(2);

            updateCurrentCoordinates();
        }

        function updateCurrentCoordinates() {
            if (!selectedNode) return;

            try {
                var transform = d3.zoomTransform(svg.node());
                var currentX = (selectedNode.x * transform.k + transform.x);
                var currentY = (selectedNode.y * transform.k + transform.y);

                var screenXEl = document.getElementById("screenX");
                var screenYEl = document.getElementById("screenY");

                if (screenXEl) screenXEl.textContent = currentX.toFixed(2);
                if (screenYEl) screenYEl.textContent = currentY.toFixed(2);
            } catch(e) {
                console.log('更新坐标时出错:', e);
            }
        }

        function clearNodeSelection() {
            selectedNode = null;
            d3.selectAll(".node").classed("selected", false);
            document.getElementById("coordinateInfo").style.display = "none";
            document.getElementById("nodeInfo").innerHTML = 
                "<h4 style='margin-top: 0;'>节点信息</h4>" +
                "<p>👆 点击左侧网络图中的任意节点查看详细信息</p>";
            updateStatus("🔄 已清除节点选择 - 点击节点查看坐标信息");
        }

        function clearAllSelections() {
            clearNodeSelection();
            clearPipeSelection();
            highlightedLinks.clear();
            updateLinkHighlights();
            d3.selectAll(".node").classed("leak", false);
            updateStatus("🧹 已清除所有选择状态");
        }

        function testCoordinates() {
            if (!selectedNode) {
                alert("请先选择一个节点");
                return;
            }

            var info = "节点坐标测试:\\n";
            info += "节点ID: " + selectedNode.id + "\\n";
            info += "数据库坐标: (" + selectedNode.original_x.toFixed(4) + ", " + selectedNode.original_y.toFixed(4) + ")\\n";
            info += "D3坐标: (" + (selectedNode.x || 0).toFixed(2) + ", " + (selectedNode.y || 0).toFixed(2) + ")\\n";

            try {
                var transform = d3.zoomTransform(svg.node());
                var screenX = (selectedNode.x * transform.k + transform.x);
                var screenY = (selectedNode.y * transform.k + transform.y);
                info += "屏幕坐标: (" + screenX.toFixed(2) + ", " + screenY.toFixed(2) + ")";
            } catch(e) {
                info += "屏幕坐标: 计算错误";
            }

            alert(info);
        }

        function onLeakTypeChange() {
            var leakType = document.getElementById("leakType").value;
            var nodeGroup = document.getElementById("nodeInputGroup");
            var pipeGroup = document.getElementById("pipeInputGroup");

            if (leakType === "节点漏损") {
                nodeGroup.style.display = "flex";
                pipeGroup.style.display = "none";
            } else {
                nodeGroup.style.display = "none";
                pipeGroup.style.display = "flex";
            }

            document.getElementById("leakNode").value = "";
            document.getElementById("leakPipe").value = "";
            resetVisualization();
        }

        async function performRealIsolation() {
            var leakType = document.getElementById("leakType").value;
            var leakTarget = "";
            var leakNodePairs = [];

            if (leakType === "节点漏损") {
                leakTarget = document.getElementById("leakNode").value.trim();
                if (!leakTarget) {
                    alert("请输入漏损节点ID");
                    return;
                }

                var targetNode = nodes.find(function(n) { return n.id === leakTarget; });
                if (!targetNode) {
                    alert("未找到指定节点");
                    return;
                }

                var connectedLinks = links.filter(function(link) {
                    var sourceId = link.source.id || link.source;
                    var targetId = link.target.id || link.target;
                    return sourceId === leakTarget || targetId === leakTarget;
                });

                leakNodePairs = connectedLinks.map(function(link) {
                    var sourceId = link.source.id || link.source;
                    var targetId = link.target.id || link.target;
                    return [sourceId, targetId];
                });

            } else if (leakType === "管道漏损" || leakType === "爆管") {
                leakTarget = document.getElementById("leakPipe").value.trim();
                if (!leakTarget) {
                    alert("请输入管道ID");
                    return;
                }

                var targetPipe = links.find(function(l) { return l.id === leakTarget; });
                if (!targetPipe) {
                    alert("未找到指定管道");
                    return;
                }

                var sourceId = targetPipe.source.id || targetPipe.source;
                var targetId = targetPipe.target.id || targetPipe.target;
                leakNodePairs = [[sourceId, targetId]];
            }

            var failValve = document.getElementById("failValve").value.trim();
            updateStatus("🔍 正在执行 " + leakType + " 隔离分析 - " + leakTarget + "...");

            resetVisualization();
            var result = await simulateIsolationAlgorithm(leakNodePairs, leakType, failValve);
            displayIsolationResult(result, leakTarget, leakType);
        }

        async function simulateIsolationAlgorithm(leakNodePairs, leakType, failValve) {
            var needCloseValves = [];
            var cutEdges = [];
            var affectedPipes = [];
            var recommendation = "";
            var isolatable = true;

            if (leakType === "爆管") {
                var leakPair = leakNodePairs[0];
                var leakPipe = links.find(function(link) {
                    var sourceId = link.source.id || link.source;
                    var targetId = link.target.id || link.target;
                    return (sourceId === leakPair[0] && targetId === leakPair[1]) ||
                           (sourceId === leakPair[1] && targetId === leakPair[0]);
                });

                if (leakPipe) {
                    var valve = valvesData[leakPipe.id];
                    if (valve && valve.status === "正常") {
                        needCloseValves = [valve.id];
                    }
                    cutEdges = [leakPair];
                    affectedPipes = [leakPipe.id];
                }

                recommendation = "爆管紧急隔离，相关用户（包括高等级用户）将临时断水，请立即抢修";

            } else {
                for (var i = 0; i < leakNodePairs.length; i++) {
                    var pair = leakNodePairs[i];
                    var start = pair[0];
                    var end = pair[1];

                    for (var j = 0; j < [start, end].length; j++) {
                        var nodeId = [start, end][j];
                        var node = nodes.find(function(n) { return n.id === nodeId; });
                        if (!node) continue;

                        var inputPipes = links.filter(function(link) {
                            var targetId = link.target.id || link.target;
                            var sourceId = link.source.id || link.source;
                            return targetId === nodeId && 
                                   !((sourceId === start && targetId === end) || 
                                     (sourceId === end && targetId === start));
                        });

                        if (node.level === 'A' && inputPipes.length === 0) {
                            isolatable = false;
                            recommendation = "A级建筑" + nodeId + "仅有一条供水，禁止隔离，必须保障供水";
                            return {
                                need_close_valves: [],
                                lost_valves: failValve ? [failValve] : [],
                                isolatable: false,
                                cut_edges: [],
                                affected_pipes: [],
                                leak_type: leakType,
                                recommendation: recommendation,
                                affected_pipes_count: 0
                            };
                        } else if (node.level === 'B' && inputPipes.length === 0) {
                            isolatable = false;
                            recommendation = "B级建筑" + nodeId + "仅有一条供水，不建议隔离，建议优先抢修";
                            return {
                                need_close_valves: [],
                                lost_valves: failValve ? [failValve] : [],
                                isolatable: false,
                                cut_edges: [],
                                affected_pipes: [],
                                leak_type: leakType,
                                recommendation: recommendation,
                                affected_pipes_count: 0
                            };
                        }
                    }
                }

                for (var i = 0; i < leakNodePairs.length; i++) {
                    var pair = leakNodePairs[i];
                    var start = pair[0];
                    var end = pair[1];

                    var affectedPipe = links.find(function(link) {
                        var sourceId = link.source.id || link.source;
                        var targetId = link.target.id || link.target;
                        return (sourceId === start && targetId === end) ||
                               (sourceId === end && targetId === start);
                    });

                    if (affectedPipe) {
                        var valve = valvesData[affectedPipe.id];
                        if (valve && valve.status === "正常") {
                            needCloseValves.push(valve.id);
                        }
                        cutEdges.push([start, end]);
                        affectedPipes.push(affectedPipe.id);
                    }
                }

                recommendation = isolatable ? "隔离成功，影响最小" : "无法隔离，需施工切断";
            }

            needCloseValves = needCloseValves.filter(function(value, index, self) {
                return self.indexOf(value) === index;
            });

            return {
                need_close_valves: needCloseValves,
                lost_valves: failValve ? [failValve] : [],
                isolatable: isolatable,
                cut_edges: cutEdges,
                affected_pipes: affectedPipes,
                leak_type: leakType,
                recommendation: recommendation,
                affected_pipes_count: cutEdges.length
            };
        }

        function displayIsolationResult(result, leakTarget, leakType) {
            currentIsolationResult = result;

            if (result.affected_pipes && result.affected_pipes.length > 0) {
                result.affected_pipes.forEach(function(pipeId) {
                    highlightedLinks.add(pipeId);
                });
                updateLinkHighlights();
            }

            if (leakType === "节点漏损") {
                d3.selectAll(".node")
                    .classed("leak", function(d) { return d.id === leakTarget; });
            } else {
                if (result.cut_edges && result.cut_edges.length > 0) {
                    result.cut_edges.forEach(function(edge) {
                        var sourceId = edge[0];
                        var targetId = edge[1];
                        d3.selectAll(".node")
                            .classed("leak", function(d) { 
                                return d.id === sourceId || d.id === targetId; 
                            });
                    });
                }
            }

            var targetInfo = leakType === "节点漏损" ? "节点: " + leakTarget : "管道: " + leakTarget;

            var resultHtml = 
                "<div class='result-panel'>" +
                "<strong>🔍 隔离分析结果</strong><br>" +
                "<strong>类型:</strong> " + result.leak_type + "<br>" +
                "<strong>目标:</strong> " + targetInfo + "<br>" +
                "<strong>可隔离:</strong> " + (result.isolatable ? "✅ 是" : "❌ 否") + "<br>" +
                "<strong>需关闭阀门:</strong> " + result.need_close_valves.length + " 个<br>";

            if (result.need_close_valves.length > 0) {
                resultHtml += "<small style='color: #666;'>阀门ID: " + result.need_close_valves.join(', ') + "</small><br>";
            }

            resultHtml += "<strong>影响管道:</strong> " + result.affected_pipes_count + " 条<br>";

            if (result.affected_pipes && result.affected_pipes.length > 0) {
                resultHtml += "<small style='color: #666;'>管道ID: " + result.affected_pipes.join(', ') + "</small><br>";
            }

            if (result.lost_valves && result.lost_valves.length > 0) {
                resultHtml += "<strong>失效阀门:</strong> " + result.lost_valves.join(', ') + "<br>";
            }

            resultHtml += "<strong>建议:</strong> " + result.recommendation + "</div>";

            if (result.affected_pipes && result.affected_pipes.length > 0) {
                resultHtml += "<h5 style='margin-top: 15px; margin-bottom: 10px;'>📋 需关闭的管道详情</h5>";
                resultHtml += "<table class='coordinate-table'>";
                resultHtml += "<tr><th>管道ID</th><th>阀门ID</th><th>状态</th></tr>";

                result.affected_pipes.forEach(function(pipeId) {
                    var valve = valvesData[pipeId];
                    var valveId = valve ? valve.id : "无阀门";
                    var valveStatus = valve ? valve.status : "N/A";
                    resultHtml += "<tr>";
                    resultHtml += "<td>" + pipeId + "</td>";
                    resultHtml += "<td>" + valveId + "</td>";
                    resultHtml += "<td>" + valveStatus + "</td>";
                    resultHtml += "</tr>";
                });

                resultHtml += "</table>";
            }

            document.getElementById("isolationResult").style.display = "block";
            document.getElementById("resultContent").innerHTML = resultHtml;

            var statusIcon = result.isolatable ? "✅" : "❌";
            updateStatus(statusIcon + " " + result.leak_type + "分析完成 - " + result.recommendation);
        }

        function resetVisualization() {
            highlightedLinks.clear();
            updateLinkHighlights();
            d3.selectAll(".node").classed("leak", false);
            document.getElementById("isolationResult").style.display = "none";
            currentIsolationResult = null;
            updateStatus("🔄 已重置 - 选择节点开始新的隔离分析");
        }

        function showAllPipes() {
            highlightedLinks.clear();
            links.forEach(function(link) {
                highlightedLinks.add(link.id);
            });
            updateLinkHighlights();
            updateStatus("👁️ 显示所有 " + links.length + " 条管道");
        }

        function updateLinkHighlights() {
            d3.selectAll(".link")
                .classed("highlighted", function(d) {
                    return highlightedLinks.has(d.id);
                })
                .attr("marker-end", function(d) {
                    return highlightedLinks.has(d.id) ? "url(#arrow-highlighted)" : "url(#arrow-normal)";
                })
                .style("stroke-dasharray", function(d) {
                    return highlightedLinks.has(d.id) ? "10,5" : "none";
                });
        }

        function updateStatus(message) {
            var statusEl = document.getElementById("status");
            if (statusEl) {
                statusEl.innerHTML = message;
            }
        }

        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;

            if (selectedNode && selectedNode.id === d.id) {
                updateCurrentCoordinates();
            }
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>"""

    # 组合完整HTML内容
    html_content = html_start + js_content

    # 保存HTML文件
    output_file = "interactive_network_visualization_complete.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ 完整版交互式可视化已生成: {output_file}")
    print(f"📊 数据统计: {len(nodes)} 个节点, {len(links)} 条管道, {len(valves)} 个阀门")

    # 尝试在浏览器中打开
    try:
        import webbrowser
        file_path = os.path.abspath(output_file)
        webbrowser.open(f'file://{file_path}')
        print(f"🌐 正在浏览器中打开: {output_file}")
    except:
        print(f"📁 请手动打开文件: {output_file}")

    return True


def create_integrated_test():
    """创建集成测试版本"""
    print("🚀 创建完整版集成版本...")

    # 读取数据并集成隔离算法
    conn = sqlite3.connect("my_database.db")
    c = conn.cursor()

    # 测试数据库连接
    try:
        c.execute("SELECT COUNT(*) FROM building_nodes")
        node_count = c.fetchone()[0]
        if node_count == 0:
            print("❌ 数据库为空，请先运行 create.py")
            return False
    except:
        print("❌ 数据库连接失败")
        return False

    conn.close()

    # 生成交互式HTML
    if generate_fixed_interactive_html():
        print("🎉 完整版集成版本创建成功！")
        print("\n📋 完整功能清单:")
        print("✅ 节点功能:")
        print("  • 点击节点查看详细信息和坐标")
        print("  • 绿色高亮选中效果")
        print("  • 三种坐标类型显示（数据库/D3/屏幕）")
        print("  • 实时坐标更新（拖拽和缩放时）")
        print("✅ 管道功能:")
        print("  • 点击管道查看详细信息和阀门")
        print("  • 蓝色高亮选中效果")
        print("  • 阀门状态显示（正常/故障）")
        print("  • 管道连接节点高亮")
        print("  • 鼠标悬停显示工具提示")
        print("✅ 隔离分析功能:")
        print("  • 完整的业务规则检查（A级/B级保护）")
        print("  • 管道标红高亮（需关闭的管道）")
        print("  • 节点标红闪烁（漏损点）")
        print("  • 详细的阀门和管道列表")
        print("  • 管道-阀门对应关系表格")
        print("✅ 交互控制:")
        print("  • 智能选择切换（点击节点清除管道选择）")
        print("  • 全局清除选择功能")
        print("  • 拖拽节点、缩放视图")
        print("  • 显示所有管道、重置视图")
        return True
    else:
        return False


if __name__ == "__main__":
    print("🔧 完整版交互式可视化生成器")
    print("=" * 50)

    choice = input("选择模式:\n1. 生成完整版交互式HTML\n2. 创建完整版集成测试\n请输入 (1-2): ").strip()

    if choice == '1':
        generate_fixed_interactive_html()
    elif choice == '2':
        create_integrated_test()
    else:
        print("❌ 无效选择")
        generate_fixed_interactive_html()  # 默认选项