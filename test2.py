# 修复版增强 test2.py - 基于简化版本的成功经验
import sqlite3
import json
import os


def generate_fixed_interactive_html():
    """生成修复版交互式HTML可视化"""
    print("🎨 正在生成修复版交互式可视化...")

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

    # 生成HTML模板 - 使用简化的字符串拼接避免模板字符串问题
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>供水网络交互式可视化 - 修复版</title>
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
            transform: scale(1.2);
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
        }

        .link.highlighted {
            stroke: #ff4444;
            stroke-width: 6px;
            stroke-opacity: 1;
            filter: drop-shadow(0 0 8px #ff4444);
            animation: flow 1s infinite linear;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚰 供水网络交互式可视化系统（修复版）</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">节点: """ + str(len(nodes)) + """ | 管道: """ + str(
        len(links)) + """ | 阀门: """ + str(len(valves)) + """ | ✨ 功能：节点坐标显示</p>
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
                </div>
            </div>

            <div class="info-panel">
                <div class="info-section" id="nodeInfo">
                    <h4 style="margin-top: 0;">节点信息</h4>
                    <p>👆 点击左侧网络图中的任意节点查看详细信息</p>
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
            ✅ 系统已加载 - 点击节点查看坐标信息
        </div>
    </div>

    <script>
        // 数据 - 使用简单的方式避免模板字符串问题
        const nodesData = """ + json.dumps(nodes, ensure_ascii=False) + """;
        const linksData = """ + json.dumps(links, ensure_ascii=False) + """;
        const valvesData = """ + json.dumps(valves, ensure_ascii=False) + """;

        // 全局变量
        let nodes = [];
        let links = [];
        let simulation;
        let svg, g;
        let highlightedLinks = new Set();
        let currentIsolationResult = null;
        let selectedNode = null;

        console.log('加载数据:', nodesData.length, '个节点,', linksData.length, '条管道');

        // 初始化
        function init() {
            // 处理数据
            nodes = nodesData.map(d => ({...d}));
            links = linksData.map(d => ({
                ...d,
                source: d.source,
                target: d.target
            }));

            svg = d3.select("#networkSvg");
            g = svg.append("g");

            // 添加缩放和拖拽
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
            const width = parseInt(svg.style("width"));
            const height = parseInt(svg.style("height"));

            // 清除现有内容
            g.selectAll("*").remove();

            // 定义箭头标记
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
                .on("click", function(event, d) {
                    const leakType = document.getElementById("leakType").value;
                    if (leakType === "管道漏损" || leakType === "爆管") {
                        document.getElementById("leakPipe").value = d.id;
                    } else {
                        toggleLinkHighlight(d.id);
                        const sourceId = d.source.id || d.source;
                        document.getElementById("leakNode").value = sourceId;
                    }
                });

            // 绘制节点 - 关键修复：简化事件处理
            const node = g.append("g")
                .selectAll("circle")
                .data(nodes)
                .enter().append("circle")
                .attr("class", "node")
                .attr("r", d => d.level === 'A' ? 12 : (d.level === 'B' ? 10 : 8))
                .attr("fill", d => d.color)
                .on("click", function(event, d) {
                    console.log('节点被点击:', d);
                    selectNodeFunction(d);
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
                .force("center", d3.forceCenter(width / 2 || 400, height / 2 || 300))
                .force("collision", d3.forceCollide().radius(d => (d.level === 'A' ? 20 : 15)));

            // 更新位置
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

                // 实时更新当前坐标
                updateCurrentCoordinates();
            });
        }

        // 选择节点功能 - 关键修复：简化函数名
        function selectNodeFunction(node) {
            console.log('选择节点:', node);
            selectedNode = node;

            // 更新节点视觉效果
            d3.selectAll(".node")
                .classed("selected", d => d.id === node.id);

            // 显示节点信息
            document.getElementById("nodeInfo").innerHTML = 
                "<h4 style='margin-top: 0;'>节点详情</h4>" +
                "<p><strong>" + node.name + "</strong></p>" +
                "<p>ID: " + node.id + "</p>" +
                "<p>等级: " + node.level + "</p>" +
                "<p>类型: " + node.type + "</p>";

            // 显示坐标信息
            document.getElementById("coordinateInfo").style.display = "block";
            updateCoordinateDisplay();

            // 设置输入框
            document.getElementById("leakNode").value = node.id;

            updateStatus("✅ 已选择节点: " + node.id + " - " + node.name);
        }

        // 更新坐标显示
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

        // 更新当前坐标
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

        // 清除节点选择
        function clearNodeSelection() {
            selectedNode = null;
            d3.selectAll(".node").classed("selected", false);
            document.getElementById("coordinateInfo").style.display = "none";
            document.getElementById("nodeInfo").innerHTML = 
                "<h4 style='margin-top: 0;'>节点信息</h4>" +
                "<p>👆 点击左侧网络图中的任意节点查看详细信息</p>";
            updateStatus("🔄 已清除节点选择 - 点击节点查看坐标信息");
        }

        // 测试坐标功能
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

        // 其他功能函数
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

                // 找出连接到该节点的所有管道
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

                console.log('节点漏损 - 节点', leakTarget, ', 影响管道:', leakNodePairs);

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

                console.log(leakType + ' - 管道', leakTarget, ', 节点对:', leakNodePairs);
            }

            var failValve = document.getElementById("failValve").value.trim();

            updateStatus("🔍 正在执行 " + leakType + " 隔离分析 - " + leakTarget + "...");

            // 重置视图
            resetVisualization();

            // 模拟调用隔离算法
            var result = await simulateIsolationAlgorithm(leakNodePairs, leakType, failValve);

            // 显示结果
            displayIsolationResult(result, leakTarget, leakType);
        }

        // 模拟隔离算法（完整版本）
        async function simulateIsolationAlgorithm(leakNodePairs, leakType, failValve) {
            console.log('模拟隔离算法:', {leakNodePairs: leakNodePairs, leakType: leakType, failValve: failValve});

            var needCloseValves = [];
            var cutEdges = [];
            var affectedPipes = [];
            var recommendation = "";
            var isolatable = true;

            if (leakType === "爆管") {
                // 爆管：无条件隔离
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
                // 普通漏损/节点漏损：检查业务规则
                for (var i = 0; i < leakNodePairs.length; i++) {
                    var pair = leakNodePairs[i];
                    var start = pair[0];
                    var end = pair[1];

                    for (var j = 0; j < [start, end].length; j++) {
                        var nodeId = [start, end][j];
                        var node = nodes.find(function(n) { return n.id === nodeId; });
                        if (!node) continue;

                        // 计算输入管道数（不含当前漏损管道）
                        var inputPipes = links.filter(function(link) {
                            var targetId = link.target.id || link.target;
                            var sourceId = link.source.id || link.source;
                            return targetId === nodeId && 
                                   !((sourceId === start && targetId === end) || 
                                     (sourceId === end && targetId === start));
                        });

                        if (node.level === 'A') {
                            if (inputPipes.length === 0) {
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
                            }
                        } else if (node.level === 'B') {
                            if (inputPipes.length === 0) {
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
                }

                // 如果通过业务规则检查，执行隔离
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

            // 去重
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

            // 高亮相关管道
            if (result.affected_pipes && result.affected_pipes.length > 0) {
                result.affected_pipes.forEach(function(pipeId) {
                    highlightedLinks.add(pipeId);
                });
                updateLinkHighlights();
            }

            // 高亮目标节点（如果是节点漏损）
            if (leakType === "节点漏损") {
                d3.selectAll(".node")
                    .classed("leak", function(d) { return d.id === leakTarget; });
            } else {
                // 高亮管道的两端节点
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

            // 显示详细结果信息
            var targetInfo = leakType === "节点漏损" ? 
                "节点: " + leakTarget : 
                "管道: " + leakTarget;

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

            // 添加管道详情表格
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
            highlightedLinks.clear(); // 先清空
            links.forEach(function(link) {
                highlightedLinks.add(link.id);
            });
            updateLinkHighlights();
            updateStatus("👁️ 显示所有 " + links.length + " 条管道");
        }

        function toggleLinkHighlight(linkId) {
            if (highlightedLinks.has(linkId)) {
                highlightedLinks.delete(linkId);
            } else {
                highlightedLinks.add(linkId);
            }
            updateLinkHighlights();
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

        // 拖拽函数
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;

            // 如果拖拽的是选中节点，实时更新坐标显示
            if (selectedNode && selectedNode.id === d.id) {
                updateCurrentCoordinates();
            }
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>"""

    # 保存HTML文件
    output_file = "interactive_network_visualization_fixed.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)

    print(f"✅ 修复版交互式可视化已生成: {output_file}")
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
    print("🚀 创建修复版集成版本...")

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
        print("🎉 修复版集成版本创建成功！")
        print("\n📋 修复内容:")
        print("✅ 解决了节点点击无反应的问题")
        print("✅ 简化了JavaScript模板字符串，避免语法错误")
        print("✅ 改进了事件处理机制")
        print("✅ 增加了调试信息和错误处理")
        print("✅ 优化了界面布局，右侧面板显示信息")
        print("\n📋 功能特性:")
        print("🎯 节点点击选择 - 绿色高亮显示")
        print("📍 三种坐标显示:")
        print("  • 数据库原始坐标")
        print("  • D3计算坐标")
        print("  • 当前屏幕坐标（考虑缩放和平移）")
        print("🔧 测试坐标功能 - 弹窗显示详细坐标信息")
        print("🧹 清除选择功能")
        print("🎮 完整的隔离分析功能")
        print("\n📋 使用方法:")
        print("1. 浏览器会自动打开交互式界面")
        print("2. 点击左侧网络图中的任意节点")
        print("3. 右侧面板会显示节点信息和坐标")
        print("4. 可以拖拽节点观察坐标变化")
        print("5. 使用'测试坐标'按钮查看详细信息")
        return True
    else:
        return False


if __name__ == "__main__":
    print("🔧 修复版交互式可视化生成器")
    print("=" * 50)

    choice = input("选择模式:\n1. 生成修复版交互式HTML\n2. 创建修复版集成测试\n请输入 (1-2): ").strip()

    if choice == '1':
        generate_fixed_interactive_html()
    elif choice == '2':
        create_integrated_test()
    else:
        print("❌ 无效选择")
        generate_fixed_interactive_html()  # 默认选项