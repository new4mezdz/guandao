# interactive_viz_generator.py - 生成交互式可视化
import sqlite3
import json
import os
from isolate_leakage import isolate_leakage


def generate_interactive_html():
    """生成交互式HTML可视化"""
    print("🎨 正在生成交互式可视化...")

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
            'x': float(node[4]) * 20,  # 缩放坐标
            'y': float(node[5]) * 20,
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

    # 生成HTML模板
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>供水网络交互式可视化 - 真实数据</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(45deg, #2196F3, #21CBF3);
            color: white;
            padding: 20px;
            text-align: center;
        }}

        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 300;
        }}

        .controls {{
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }}

        .control-group {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        select, input, button {{
            padding: 10px 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
        }}

        button {{
            background: linear-gradient(45deg, #007bff, #0056b3);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 500;
        }}

        button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,123,255,0.3);
        }}

        .viz-container {{
            position: relative;
            height: 700px;
            overflow: hidden;
            background: #fafafa;
        }}

        svg {{
            width: 100%;
            height: 100%;
            cursor: grab;
        }}

        svg:active {{
            cursor: grabbing;
        }}

        .node {{
            stroke: #fff;
            stroke-width: 3px;
            cursor: pointer;
            transition: all 0.3s;
            filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.2));
        }}

        .node:hover {{
            stroke-width: 4px;
            transform: scale(1.2);
        }}

        .node.leak {{
            stroke: #ff0000;
            stroke-width: 5px;
            filter: drop-shadow(0 0 10px #ff0000);
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.1); }}
            100% {{ transform: scale(1); }}
        }}

        .link {{
            stroke: #999;
            stroke-opacity: 0.8;
            stroke-width: 3px;
            fill: none;
            transition: all 0.3s;
        }}

        .link.highlighted {{
            stroke: #ff4444;
            stroke-width: 6px;
            stroke-opacity: 1;
            filter: drop-shadow(0 0 8px #ff4444);
            animation: flow 1s infinite linear;
        }}

        @keyframes flow {{
            0% {{ stroke-dashoffset: 0; }}
            100% {{ stroke-dashoffset: 20; }}
        }}

        .arrow {{
            fill: #666;
            transition: all 0.3s;
        }}

        .arrow.highlighted {{
            fill: #ff4444;
        }}

        .node-label {{
            font-size: 12px;
            font-weight: bold;
            text-anchor: middle;
            pointer-events: none;
            fill: #333;
            text-shadow: 1px 1px 2px white;
        }}

        .tooltip {{
            position: absolute;
            background: linear-gradient(45deg, rgba(0,0,0,0.9), rgba(50,50,50,0.9));
            color: white;
            padding: 12px;
            border-radius: 8px;
            font-size: 13px;
            pointer-events: none;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}

        .legend, .info-panel {{
            position: absolute;
            background: rgba(255,255,255,0.95);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }}

        .legend {{
            top: 20px;
            right: 20px;
            min-width: 150px;
        }}

        .info-panel {{
            bottom: 20px;
            left: 20px;
            min-width: 250px;
            max-width: 300px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            font-size: 13px;
        }}

        .legend-color {{
            width: 18px;
            height: 18px;
            border-radius: 50%;
            margin-right: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}

        .status {{
            padding: 15px 20px;
            text-align: center;
            background: linear-gradient(45deg, #e9ecef, #f8f9fa);
            font-size: 14px;
            font-weight: 500;
        }}

        .result-panel {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚰 供水网络交互式可视化系统 </h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">节点: {len(nodes)} | 管道: {len(links)} | 阀门: {len(valves)}</p>
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
                <input type="text" id="leakNode" placeholder="如: N001" list="nodeList">
                <datalist id="nodeList">
                    {' '.join([f'<option value="{node["id"]}">' for node in nodes])}
                </datalist>
            </div>

            <div class="control-group" id="pipeInputGroup" style="display: none;">
                <label><strong>漏损管道:</strong></label>
                <input type="text" id="leakPipe" placeholder="如: P0001" list="pipeList">
                <datalist id="pipeList">
                    {' '.join([f'<option value="{link["id"]}">' for link in links])}
                </datalist>
            </div>

            <div class="control-group">
                <label><strong>失效阀门:</strong></label>
                <input type="text" id="failValve" placeholder="如: V0001 (可选)">
            </div>

            <button onclick="performRealIsolation()">🔍 执行隔离分析</button>
            <button onclick="resetVisualization()">🔄 重置视图</button>
            <button onclick="showAllPipes()">👁️ 显示所有管道</button>
            <button onclick="exportResult()">📋 导出结果</button>
        </div>

        <div class="viz-container">
            <svg id="networkSvg"></svg>

            <div class="legend">
                <h4 style="margin-top: 0;">图例</h4>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ff4444;"></div>
                    <span>A级 水厂 ({[node for node in nodes if node['level'] == 'A'].__len__()})</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ff8800;"></div>
                    <span>B级 学校 ({[node for node in nodes if node['level'] == 'B'].__len__()})</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #44ff44;"></div>
                    <span>C级 住宅 ({[node for node in nodes if node['level'] == 'C'].__len__()})</span>
                </div>
                <hr style="margin: 15px 0;">
                <div class="legend-item">
                    <div style="width: 20px; height: 4px; background: #ff4444; margin-right: 8px; border-radius: 2px;"></div>
                    <span>需关闭管道</span>
                </div>
                <div class="legend-item">
                    <div style="width: 20px; height: 3px; background: #999; margin-right: 8px; border-radius: 2px;"></div>
                    <span>正常管道</span>
                </div>
            </div>

            <div class="info-panel">
                <div id="nodeInfo">
                    <h4 style="margin-top: 0;">节点信息</h4>
                    <p>点击任意节点查看详细信息</p>
                </div>
                <div id="isolationResult" style="display: none;">
                    <h4 style="margin-top: 15px; color: #d63384;">隔离结果</h4>
                    <div id="resultContent"></div>
                </div>
            </div>

            <div class="tooltip" id="tooltip"></div>
        </div>

        <div class="status" id="status">
            ✅ 系统已加载真实数据 - 选择节点开始隔离分析
        </div>
    </div>

    <script>
        // 真实数据
        const nodesData = {json.dumps(nodes, ensure_ascii=False, indent=2)};
        const linksData = {json.dumps(links, ensure_ascii=False, indent=2)};
        const valvesData = {json.dumps(valves, ensure_ascii=False, indent=2)};

        // 全局变量
        let nodes = [];
        let links = [];
        let simulation;
        let svg, g;
        let highlightedLinks = new Set();
        let currentIsolationResult = null;

        // 初始化
        function init() {{
            console.log('加载数据:', nodesData.length, '个节点,', linksData.length, '条管道');

            // 处理数据
            nodes = nodesData.map(d => ({{...d}}));
            links = linksData.map(d => ({{
                ...d,
                source: d.source,
                target: d.target
            }}));

            svg = d3.select("#networkSvg");
            g = svg.append("g");

            // 添加缩放和拖拽
            const zoom = d3.zoom()
                .scaleExtent([0.1, 4])
                .on("zoom", (event) => {{
                    g.attr("transform", event.transform);
                }});

            svg.call(zoom);

            updateVisualization();
        }}

        // 更新可视化
        function updateVisualization() {{
            // 清除现有内容
            g.selectAll("*").remove();

            // 定义箭头标记
            svg.select("defs").remove();
            svg.append("defs").selectAll("marker")
                .data(["normal", "highlighted"])
                .enter().append("marker")
                .attr("id", d => `arrow-${{d}}`)
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
                .attr("id", d => `link-${{d.id}}`)
                .attr("marker-end", "url(#arrow-normal)")
                .attr("stroke-width", d => Math.max(2, d.diameter / 100))
                .on("mouseover", function(event, d) {{
                    const valve = valvesData[d.id];
                    const content = `管道: ${{d.id}}<br>
                                   直径: ${{d.diameter}}mm<br>
                                   状态: ${{d.status}}<br>
                                   ${{valve ? `阀门: ${{valve.id}} (${{valve.status}})` : '无阀门'}}`;
                    showTooltip(event, content);
                }})
                .on("mouseout", hideTooltip)
                .on("click", function(event, d) {{
                    const leakType = document.getElementById("leakType").value;
                    if (leakType === "管道漏损" || leakType === "爆管") {{
                        document.getElementById("leakPipe").value = d.id;
                    }} else {{
                        toggleLinkHighlight(d.id);
                        // 如果是节点漏损模式，点击管道时选择其中一个节点
                        const sourceId = d.source.id || d.source;
                        document.getElementById("leakNode").value = sourceId;
                    }}
                }});

            // 绘制节点
            const node = g.append("g")
                .selectAll("circle")
                .data(nodes)
                .enter().append("circle")
                .attr("class", "node")
                .attr("r", d => d.level === 'A' ? 12 : (d.level === 'B' ? 10 : 8))
                .attr("fill", d => d.color)
                .on("mouseover", function(event, d) {{
                    const content = `${{d.name}}<br>
                                   ID: ${{d.id}}<br>
                                   等级: ${{d.level}}<br>
                                   类型: ${{d.type}}`;
                    showTooltip(event, content);
                }})
                .on("mouseout", hideTooltip)
                .on("click", function(event, d) {{
                    showNodeInfo(d);
                    document.getElementById("leakNode").value = d.id;
                }})
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
                .force("center", d3.forceCenter(800, 350))
                .force("collision", d3.forceCollide().radius(d => (d.level === 'A' ? 20 : 15)));

            // 更新位置
            simulation.on("tick", () => {{
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
            }});
        }}

        // 漏损类型切换处理
        function onLeakTypeChange() {{
            const leakType = document.getElementById("leakType").value;
            const nodeGroup = document.getElementById("nodeInputGroup");
            const pipeGroup = document.getElementById("pipeInputGroup");

            if (leakType === "节点漏损") {{
                nodeGroup.style.display = "flex";
                pipeGroup.style.display = "none";
                document.getElementById("leakNode").placeholder = "输入节点ID, 如: N001";
            }} else if (leakType === "管道漏损" || leakType === "爆管") {{
                nodeGroup.style.display = "none";
                pipeGroup.style.display = "flex";
                document.getElementById("leakPipe").placeholder = leakType === "爆管" ? "输入爆管管道ID, 如: P0001" : "输入漏损管道ID, 如: P0001";
            }}

            // 清空输入
            document.getElementById("leakNode").value = "";
            document.getElementById("leakPipe").value = "";

            resetVisualization();
        }}

        // 执行真实隔离分析
        async function performRealIsolation() {{
            const leakType = document.getElementById("leakType").value;
            let leakTarget = "";
            let leakNodePairs = [];

            if (leakType === "节点漏损") {{
                leakTarget = document.getElementById("leakNode").value.trim();
                if (!leakTarget) {{
                    alert("请输入漏损节点ID");
                    return;
                }}

                const targetNode = nodes.find(n => n.id === leakTarget);
                if (!targetNode) {{
                    alert("未找到指定节点");
                    return;
                }}

                // 找出连接到该节点的所有管道
                const connectedLinks = links.filter(link => 
                    link.source.id === leakTarget || link.target.id === leakTarget ||
                    link.source === leakTarget || link.target === leakTarget
                );

                leakNodePairs = connectedLinks.map(link => {{
                    const sourceId = link.source.id || link.source;
                    const targetId = link.target.id || link.target;
                    return sourceId === leakTarget ? [sourceId, targetId] : [sourceId, targetId];
                }});

                console.log(`节点漏损 - 节点 ${{leakTarget}}, 影响管道:`, leakNodePairs);

            }} else if (leakType === "管道漏损" || leakType === "爆管") {{
                leakTarget = document.getElementById("leakPipe").value.trim();
                if (!leakTarget) {{
                    alert("请输入管道ID");
                    return;
                }}

                const targetPipe = links.find(l => l.id === leakTarget);
                if (!targetPipe) {{
                    alert("未找到指定管道");
                    return;
                }}

                const sourceId = targetPipe.source.id || targetPipe.source;
                const targetId = targetPipe.target.id || targetPipe.target;
                leakNodePairs = [[sourceId, targetId]];

                console.log(`${{leakType}} - 管道 ${{leakTarget}}, 节点对:`, leakNodePairs);
            }}

            const failValve = document.getElementById("failValve").value.trim();

            updateStatus(`🔍 正在执行 ${{leakType}} 隔离分析 - ${{leakTarget}}...`);

            // 重置视图
            resetVisualization();

            // 模拟调用隔离算法
            const result = await simulateIsolationAlgorithm(leakNodePairs, leakType, failValve);

            // 显示结果
            displayIsolationResult(result, leakTarget, leakType);
        }}

        // 模拟隔离算法（更完整的版本）
        async function simulateIsolationAlgorithm(leakNodePairs, leakType, failValve) {{
            console.log('模拟隔离算法:', {{leakNodePairs, leakType, failValve}});

            let needCloseValves = [];
            let cutEdges = [];
            let recommendation = "";
            let isolatable = true;

            if (leakType === "爆管") {{
                // 爆管：无条件隔离
                const leakPair = leakNodePairs[0];
                const leakPipe = links.find(link => {{
                    const sourceId = link.source.id || link.source;
                    const targetId = link.target.id || link.target;
                    return (sourceId === leakPair[0] && targetId === leakPair[1]) ||
                           (sourceId === leakPair[1] && targetId === leakPair[0]);
                }});

                if (leakPipe) {{
                    const valve = valvesData[leakPipe.id];
                    if (valve && valve.status === "正常") {{
                        needCloseValves = [valve.id];
                    }}
                    cutEdges = [leakPair];
                }}

                recommendation = "爆管紧急隔离，相关用户（包括高等级用户）将临时断水，请立即抢修";

            }} else {{
                // 普通漏损/节点漏损：检查业务规则
                for (const [start, end] of leakNodePairs) {{
                    for (const nodeId of [start, end]) {{
                        const node = nodes.find(n => n.id === nodeId);
                        if (!node) continue;

                        // 计算输入管道数（不含当前漏损管道）
                        const inputPipes = links.filter(link => {{
                            const targetId = link.target.id || link.target;
                            const sourceId = link.source.id || link.source;
                            return targetId === nodeId && 
                                   !((sourceId === start && targetId === end) || 
                                     (sourceId === end && targetId === start));
                        }});

                        if (node.level === 'A') {{
                            if (inputPipes.length === 0) {{
                                isolatable = false;
                                recommendation = `A级建筑${{nodeId}}仅有一条供水，禁止隔离，必须保障供水`;
                                return {{
                                    need_close_valves: [],
                                    lost_valves: failValve ? [failValve] : [],
                                    isolatable: false,
                                    cut_edges: [],
                                    leak_type: leakType,
                                    recommendation: recommendation,
                                    affected_pipes: 0
                                }};
                            }}
                        }} else if (node.level === 'B') {{
                            if (inputPipes.length === 0) {{
                                isolatable = false;
                                recommendation = `B级建筑${{nodeId}}仅有一条供水，不建议隔离，建议优先抢修`;
                                return {{
                                    need_close_valves: [],
                                    lost_valves: failValve ? [failValve] : [],
                                    isolatable: false,
                                    cut_edges: [],
                                    leak_type: leakType,
                                    recommendation: recommendation,
                                    affected_pipes: 0
                                }};
                            }}
                        }}
                    }}
                }}

                // 如果通过业务规则检查，执行隔离
                for (const [start, end] of leakNodePairs) {{
                    const affectedPipe = links.find(link => {{
                        const sourceId = link.source.id || link.source;
                        const targetId = link.target.id || link.target;
                        return (sourceId === start && targetId === end) ||
                               (sourceId === end && targetId === start);
                    }});

                    if (affectedPipe) {{
                        const valve = valvesData[affectedPipe.id];
                        if (valve && valve.status === "正常") {{
                            needCloseValves.push(valve.id);
                        }}
                        cutEdges.push([start, end]);
                    }}
                }}

                recommendation = isolatable ? "隔离成功，影响最小" : "无法隔离，需施工切断";
            }}

            return {{
                need_close_valves: [...new Set(needCloseValves)], // 去重
                lost_valves: failValve ? [failValve] : [],
                isolatable: isolatable,
                cut_edges: cutEdges,
                leak_type: leakType,
                recommendation: recommendation,
                affected_pipes: cutEdges.length
            }};
        }}

        // 显示隔离结果
        function displayIsolationResult(result, leakTarget, leakType) {{
            currentIsolationResult = result;

            // 高亮相关管道
            const affectedPipes = result.cut_edges.map(edge => {{
                return links.find(link => {{
                    const sourceId = link.source.id || link.source;
                    const targetId = link.target.id || link.target;
                    return (sourceId === edge[0] && targetId === edge[1]) ||
                           (sourceId === edge[1] && targetId === edge[0]);
                }});
            }}).filter(Boolean);

            affectedPipes.forEach(pipe => {{
                if (pipe) highlightedLinks.add(pipe.id);
            }});

            updateLinkHighlights();

            // 高亮目标节点（如果是节点漏损）
            if (leakType === "节点漏损") {{
                d3.selectAll(".node")
                    .classed("leak", d => d.id === leakTarget);
            }} else {{
                // 高亮管道的两端节点
                affectedPipes.forEach(pipe => {{
                    const sourceId = pipe.source.id || pipe.source;
                    const targetId = pipe.target.id || pipe.target;
                    d3.selectAll(".node")
                        .classed("leak", d => d.id === sourceId || d.id === targetId);
                }});
            }}

            // 显示结果信息
            const targetInfo = leakType === "节点漏损" ? 
                `节点: ${{leakTarget}}` : 
                `管道: ${{leakTarget}}`;

            const resultHtml = `
                <div class="result-panel">
                    <strong>🔍 隔离分析结果</strong><br>
                    <strong>类型:</strong> ${{result.leak_type}}<br>
                    <strong>目标:</strong> ${{targetInfo}}<br>
                    <strong>可隔离:</strong> ${{result.isolatable ? '✅ 是' : '❌ 否'}}<br>
                    <strong>需关闭阀门:</strong> ${{result.need_close_valves.length}} 个<br>
                    ${{result.need_close_valves.length > 0 ? `<small>(${{result.need_close_valves.join(', ')}})</small><br>` : ''}}
                    <strong>影响管道:</strong> ${{result.affected_pipes}} 条<br>
                    ${{result.lost_valves.length > 0 ? `<strong>失效阀门:</strong> ${{result.lost_valves.join(', ')}}<br>` : ''}}
                    <strong>建议:</strong> ${{result.recommendation}}
                </div>
            `;

            document.getElementById("isolationResult").style.display = "block";
            document.getElementById("resultContent").innerHTML = resultHtml;

            const statusIcon = result.isolatable ? '✅' : '❌';
            const statusColor = result.isolatable ? '#28a745' : '#dc3545';
            updateStatus(`${{statusIcon}} ${{result.leak_type}}分析完成 - ${{result.recommendation}}`);
        }}

        // 其他辅助函数
        function resetVisualization() {{
            highlightedLinks.clear();
            updateLinkHighlights();

            d3.selectAll(".node").classed("leak", false);
            document.getElementById("isolationResult").style.display = "none";
            currentIsolationResult = null;

            updateStatus("🔄 已重置 - 选择节点开始新的隔离分析");
        }}

        function showAllPipes() {{
            links.forEach(link => highlightedLinks.add(link.id));
            updateLinkHighlights();
            updateStatus(`👁️ 显示所有 ${{links.length}} 条管道`);
        }}

        function exportResult() {{
            if (!currentIsolationResult) {{
                alert("请先执行隔离分析");
                return;
            }}

            const exportData = {{
                timestamp: new Date().toLocaleString('zh-CN'),
                ...currentIsolationResult
            }};

            const blob = new Blob([JSON.stringify(exportData, null, 2)], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `isolation_result_${{new Date().getTime()}}.json`;
            a.click();
        }}

        function toggleLinkHighlight(linkId) {{
            if (highlightedLinks.has(linkId)) {{
                highlightedLinks.delete(linkId);
            }} else {{
                highlightedLinks.add(linkId);
            }}
            updateLinkHighlights();
        }}

        function updateLinkHighlights() {{
            d3.selectAll(".link")
                .classed("highlighted", d => highlightedLinks.has(d.id))
                .attr("marker-end", d => 
                    highlightedLinks.has(d.id) ? "url(#arrow-highlighted)" : "url(#arrow-normal)"
                )
                .style("stroke-dasharray", d => 
                    highlightedLinks.has(d.id) ? "10,5" : "none"
                );
        }}

        function showTooltip(event, content) {{
            const tooltip = d3.select("#tooltip");
            tooltip.html(content)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px")
                .style("opacity", 1);
        }}

        function hideTooltip() {{
            d3.select("#tooltip").style("opacity", 0);
        }}

        function showNodeInfo(node) {{
            const info = document.getElementById("nodeInfo");
            info.innerHTML = `
                <h4 style="margin-top: 0;">节点详情</h4>
                <strong>${{node.name}}</strong><br>
                ID: ${{node.id}}<br>
                等级: ${{node.level}}<br>
                类型: ${{node.type}}<br>
                坐标: (${{node.x.toFixed(1)}}, ${{node.y.toFixed(1)}})
            `;
        }}

        function updateStatus(message) {{
            document.getElementById("status").innerHTML = message;
        }}

        // 拖拽函数
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}

        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>"""

    # 保存HTML文件
    output_file = "interactive_network_visualization.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)

    print(f"✅ 交互式可视化已生成: {output_file}")
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
    print("🚀 创建集成版本...")

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
    if generate_interactive_html():
        print("🎉 集成版本创建成功！")
        print("\n📋 使用说明:")
        print("1. 浏览器会自动打开交互式界面")
        print("2. 点击节点选择漏损位置")
        print("3. 选择漏损类型并点击'执行隔离分析'")
        print("4. 查看高亮的需关闭管道")
        print("5. 可以拖拽节点、缩放视图")
        print("6. 导出分析结果")
        return True
    else:
        return False


if __name__ == "__main__":
    print("🎨 交互式可视化生成器")
    print("=" * 50)

    choice = input("选择模式:\n1. 生成交互式HTML\n2. 创建集成测试\n请输入 (1-2): ").strip()

    if choice == '1':
        generate_interactive_html()
    elif choice == '2':
        create_integrated_test()
    else:
        print("❌ 无效选择")
        generate_interactive_html()  # 默认选项