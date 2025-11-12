from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# 配置数据库路径
DATABASE_PATH = 'D:/9090/guandao/1.db'


@app.route('/')
def index():
    """地图标注页面 - 使用OSM地图"""
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>管道节点地图标注</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
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

        .main-content {
            display: flex;
            height: 700px;
        }

        .map-container {
            flex: 1;
            position: relative;
            overflow: hidden;
        }

        #map {
            width: 100%;
            height: 100%;
        }

        .form-panel {
            width: 350px;
            background: white;
            border-left: 1px solid #e9ecef;
            padding: 20px;
            overflow-y: auto;
        }

        .form-panel h3 {
            margin-top: 0;
            color: #2196F3;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
        }

        .form-group {
            margin-bottom: 15px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #555;
        }

        .form-group input,
        .form-group select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
            box-sizing: border-box;
        }

        .form-group input:focus,
        .form-group select:focus {
            border-color: #2196F3;
            outline: none;
            box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
        }

        .form-group input[readonly] {
            background: #f5f5f5;
            color: #888;
        }

        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }

        button {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
        }

        .btn-primary {
            background: linear-gradient(45deg, #007bff, #0056b3);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,123,255,0.3);
        }

        .btn-secondary {
            background: #6c757d;
            color: white;
        }

        .btn-secondary:hover {
            background: #5a6268;
        }

        .btn-info {
            background: #17a2b8;
            color: white;
        }

        .btn-info:hover {
            background: #138496;
        }

        .status-box {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            font-size: 14px;
        }

        .status-box.success {
            background: #d4edda;
            border-left-color: #28a745;
            color: #155724;
        }

        .status-box.error {
            background: #f8d7da;
            border-left-color: #dc3545;
            color: #721c24;
        }

        .nodes-list {
            margin-top: 20px;
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 10px;
            background: #fafafa;
        }

        .node-item {
            padding: 8px;
            margin-bottom: 5px;
            background: white;
            border-radius: 4px;
            font-size: 12px;
            border-left: 3px solid #2196F3;
            cursor: pointer;
            transition: all 0.2s;
        }

        .node-item:hover {
            background: #e7f3ff;
            transform: translateX(5px);
        }

        .leaflet-popup-content {
            font-size: 14px;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🗺️ 管道节点地图标注系统 (OpenStreetMap)</h1>
        </div>

        <div class="main-content">
            <div class="map-container">
                <div id="map"></div>
            </div>

            <div class="form-panel">
                <h3>📝 标注信息</h3>

                <div class="form-group">
                    <label>标注类型</label>
                    <select id="annotationType" onchange="switchAnnotationType()">
                        <option value="node">节点标注</option>
                        <option value="pipe">管道标注</option>
                    </select>
                </div>

                <div id="nodeForm">
                    <div class="form-group">
                        <label>节点ID *</label>
                        <input type="text" id="nodeId" placeholder="例如: N001">
                    </div>

                    <div class="form-group">
                        <label>节点名称 *</label>
                        <input type="text" id="nodeName" placeholder="例如: 主水箱">
                    </div>

                    <div class="form-group">
                        <label>节点类型</label>
                        <select id="nodeType">
                            <option value="水箱">水箱</option>
                            <option value="用户节点">用户节点</option>
                            <option value="连接节点">连接节点</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>等级</label>
                        <select id="level">
                            <option value="A">A级</option>
                            <option value="B">B级</option>
                            <option value="C">C级</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>纬度</label>
                        <input type="text" id="locLat" readonly>
                    </div>

                    <div class="form-group">
                        <label>经度</label>
                        <input type="text" id="locLng" readonly>
                    </div>
                </div>

                <div id="pipeForm" style="display: none;">
                    <div class="form-group">
                        <label>管道ID *</label>
                        <input type="text" id="pipeId" placeholder="例如: P001">
                    </div>

                    <div class="form-group">
                        <label>起始节点ID *</label>
                        <input type="text" id="startNodeId" placeholder="点击地图上第一个节点" readonly>
                    </div>

                    <div class="form-group">
                        <label>结束节点ID *</label>
                        <input type="text" id="endNodeId" placeholder="点击地图上第二个节点" readonly>
                    </div>

                    <div class="form-group">
                        <label>管径 (mm)</label>
                        <input type="number" id="diameter" placeholder="例如: 100" value="100">
                    </div>

                    <div class="form-group">
                        <label>状态</label>
                        <select id="pipeStatus">
                            <option value="正常">正常</option>
                            <option value="维修">维修</option>
                            <option value="停用">停用</option>
                        </select>
                    </div>
                </div>

                <div class="button-group">
                    <button class="btn-primary" onclick="submitAnnotation()">💾 提交</button>
                    <button class="btn-secondary" onclick="clearForm()">🔄 清空</button>
                </div>

                <div class="button-group">
                    <button class="btn-info" onclick="loadExistingNodes()">📋 加载节点</button>
                </div>

                <div class="status-box" id="statusMsg">
                    👆 点击地图选择位置
                </div>

                <div class="nodes-list" id="nodesList" style="display: none;">
                    <strong>已标注节点:</strong>
                    <div id="nodesContent"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 初始化地图 - 默认中心在中国
       const map = L.map('map').setView([30.5785, 103.9470], 13);

        // 添加OSM图层
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(map);

        let annotationType = 'node';
        let currentLat = 0;
        let currentLng = 0;
        let existingNodes = [];
        let nodeMarkers = [];
        let pipeLines = [];
        let tempMarker = null;
        let pipeClickCount = 0;
        let pipeStartNode = null;
        let pipeEndNode = null;
        let tempLine = null;

        // 定义节点图标
        function getNodeIcon(level) {
            const colors = {'A': 'red', 'B': 'orange', 'C': 'green'};
            return L.divIcon({
                className: 'custom-div-icon',
                html: `<div style="background-color: ${colors[level] || 'gray'}; width: 15px; height: 15px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
                iconSize: [15, 15],
                iconAnchor: [7.5, 7.5]
            });
        }

        // 点击地图事件
        map.on('click', function(e) {
            if (annotationType === 'node') {
                // 节点标注
                currentLat = e.latlng.lat;
                currentLng = e.latlng.lng;

                document.getElementById('locLat').value = currentLat.toFixed(6);
                document.getElementById('locLng').value = currentLng.toFixed(6);

                // 移除旧的临时标记
                if (tempMarker) {
                    map.removeLayer(tempMarker);
                }

                // 添加新的临时标记
                tempMarker = L.marker([currentLat, currentLng], {
                    icon: L.divIcon({
                        className: 'custom-div-icon',
                        html: '<div style="background-color: yellow; width: 20px; height: 20px; border-radius: 50%; border: 3px solid red; box-shadow: 0 0 10px rgba(255,0,0,0.5);"></div>',
                        iconSize: [20, 20],
                        iconAnchor: [10, 10]
                    })
                }).addTo(map);

                updateStatus('已选择坐标: (' + currentLat.toFixed(6) + ', ' + currentLng.toFixed(6) + ')', 'info');
            } else {
                // 管道标注 - 查找最近的节点
                let nearestNode = findNearestNode(e.latlng.lat, e.latlng.lng);

                if (!nearestNode) {
                    updateStatus('❌ 附近没有节点(50米内),请先标注节点', 'error');
                    return;
                }

                if (pipeClickCount === 0) {
                    pipeStartNode = nearestNode;
                    document.getElementById('startNodeId').value = nearestNode.node_id;
                    pipeClickCount = 1;

                    // 高亮起始节点
                    highlightNode(nearestNode, 'blue');

                    updateStatus('✅ 已选择起始节点: ' + nearestNode.node_id + ', 请点击结束节点', 'info');
                } else {
                    pipeEndNode = nearestNode;
                    document.getElementById('endNodeId').value = nearestNode.node_id;

                    // 高亮结束节点
                    highlightNode(nearestNode, 'green');

                    // 绘制临时连接线
                    if (tempLine) {
                        map.removeLayer(tempLine);
                    }
                    tempLine = L.polyline([
                        [pipeStartNode.location_x, pipeStartNode.location_y],
                        [pipeEndNode.location_x, pipeEndNode.location_y]
                    ], {
                        color: 'red',
                        weight: 4,
                        dashArray: '10, 5'
                    }).addTo(map);

                    pipeClickCount = 0;
                    updateStatus('✅ 已选择管道: ' + pipeStartNode.node_id + ' → ' + pipeEndNode.node_id, 'success');
                }
            }
        });

        // 高亮节点
        function highlightNode(node, color) {
            L.marker([node.location_x, node.location_y], {
                icon: L.divIcon({
                    className: 'custom-div-icon',
                    html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 15px ${color};"></div>`,
                    iconSize: [20, 20],
                    iconAnchor: [10, 10]
                })
            }).addTo(map);
        }

        // 查找最近的节点
        function findNearestNode(lat, lng) {
            let nearest = null;
            let minDist = 0.0005; // 约50米

            existingNodes.forEach(node => {
                // 注意：这里使用 node.location_x, node.location_y 已经是 Leaflet 期望的 (纬度, 经度) 顺序
                const dist = Math.sqrt(
                    Math.pow(node.location_x - lat, 2) + 
                    Math.pow(node.location_y - lng, 2)
                );
                if (dist < minDist) {
                    minDist = dist;
                    nearest = node;
                }
            });

            return nearest;
        }

        // 切换标注类型
        function switchAnnotationType() {
            annotationType = document.getElementById('annotationType').value;

            if (annotationType === 'node') {
                document.getElementById('nodeForm').style.display = 'block';
                document.getElementById('pipeForm').style.display = 'none';
                updateStatus('👆 点击地图选择节点位置', 'info');
            } else {
                document.getElementById('nodeForm').style.display = 'none';
                document.getElementById('pipeForm').style.display = 'block';
                pipeClickCount = 0;
                pipeStartNode = null;
                pipeEndNode = null;
                if (tempLine) {
                    map.removeLayer(tempLine);
                }
                updateStatus('👆 先点击起始节点,再点击结束节点', 'info');
            }
            clearForm();
        }

        // 提交标注
        function submitAnnotation() {
            if (annotationType === 'node') {
                submitNodeAnnotation();
            } else {
                submitPipeAnnotation();
            }
        }

        // 提交节点
        function submitNodeAnnotation() {
            const data = {
                node_id: document.getElementById('nodeId').value.trim(),
                node_name: document.getElementById('nodeName').value.trim(),
                node_type: document.getElementById('nodeType').value,
                level: document.getElementById('level').value,
                // 这里发送到后端时，要保证 Location_X 是经度，Location_Y 是纬度
                // 这样才能和数据库的列名匹配
                location_x: parseFloat(document.getElementById('locLng').value), // 经度 (X)
                location_y: parseFloat(document.getElementById('locLat').value)  // 纬度 (Y)
            };

            if (!data.node_id || !data.node_name) {
                updateStatus('❌ 请填写节点ID和名称!', 'error');
                return;
            }

            if (!data.location_x || !data.location_y) {
                updateStatus('❌ 请先在地图上选择位置!', 'error');
                return;
            }

            fetch('/api/add-node', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    updateStatus('✅ 节点保存成功: ' + data.node_id, 'success');
                    clearForm();
                    loadExistingNodes();
                } else {
                    updateStatus('❌ 保存失败: ' + result.error, 'error');
                }
            })
            .catch(error => {
                updateStatus('❌ 网络错误: ' + error, 'error');
            });
        }

        // 提交管道
        function submitPipeAnnotation() {
            const data = {
                pipe_id: document.getElementById('pipeId').value.trim(),
                start_node_id: document.getElementById('startNodeId').value.trim(),
                end_node_id: document.getElementById('endNodeId').value.trim(),
                diameter: parseFloat(document.getElementById('diameter').value),
                status: document.getElementById('pipeStatus').value
            };

            if (!data.pipe_id || !data.start_node_id || !data.end_node_id) {
                updateStatus('❌ 请填写完整的管道信息!', 'error');
                return;
            }

            fetch('/api/add-pipe', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    updateStatus('✅ 管道保存成功: ' + data.pipe_id, 'success');
                    clearForm();
                    loadPipes();
                } else {
                    updateStatus('❌ 保存失败: ' + result.error, 'error');
                }
            })
            .catch(error => {
                updateStatus('❌ 网络错误: ' + error, 'error');
            });
        }

        // 清空表单
        function clearForm() {
            if (annotationType === 'node') {
                document.getElementById('nodeId').value = '';
                document.getElementById('nodeName').value = '';
                document.getElementById('locLat').value = '';
                document.getElementById('locLng').value = '';
                currentLat = 0;
                currentLng = 0;
                if (tempMarker) {
                    map.removeLayer(tempMarker);
                    tempMarker = null;
                }
            } else {
                document.getElementById('pipeId').value = '';
                document.getElementById('startNodeId').value = '';
                document.getElementById('endNodeId').value = '';
                pipeClickCount = 0;
                pipeStartNode = null;
                pipeEndNode = null;
                if (tempLine) {
                    map.removeLayer(tempLine);
                    tempLine = null;
                }
                // 重新加载以清除高亮
                loadExistingNodes();
            }
        }

        // 加载已有节点
        function loadExistingNodes() {
            fetch('/api/get-nodes')
                .then(response => response.json())
                .then(data => {
                    existingNodes = data.nodes;

                    // 清除旧标记
                    nodeMarkers.forEach(marker => map.removeLayer(marker));
                    nodeMarkers = [];

                    // 添加新标记
                    existingNodes.forEach(node => {
                       // Leaflet 期望 (纬度, 经度)。由于后端已将 location_x 设为纬度，location_y 设为经度，所以顺序是 (x, y)
                       const marker = L.marker([node.location_x, node.location_y], { 
                            icon: getNodeIcon(node.level)
                        }).addTo(map);

                        marker.bindPopup(`
                            <b>${node.node_id}</b><br>
                            ${node.node_name}<br>
                            类型: ${node.node_type}<br>
                            等级: ${node.level}
                        `);

                        nodeMarkers.push(marker);
                    });

                    // 显示节点列表
                    const listDiv = document.getElementById('nodesList');
                    const contentDiv = document.getElementById('nodesContent');

                    if (existingNodes.length > 0) {
                        listDiv.style.display = 'block';
                        contentDiv.innerHTML = existingNodes.map(node => 
                            `<div class="node-item" onclick="zoomToNode(${node.location_x}, ${node.location_y})"">${node.node_id} - ${node.node_name} (${node.level}级)</div>`
                        ).join('');

                        // 自动调整地图以显示所有节点
                        if (existingNodes.length > 0) {
                            // Leaflet 期望 (纬度, 经度)，因此使用 (location_y, location_x)
                            const bounds = L.latLngBounds(existingNodes.map(n => [n.location_x, n.location_y]));
                            map.fitBounds(bounds, {padding: [50, 50]});
                        }
                    } else {
                        listDiv.style.display = 'none';
                    }

                    updateStatus('📊 已加载 ' + existingNodes.length + ' 个节点', 'success');

                    // 同时加载管道
                    loadPipes();
                });
        }

        // 加载管道
        function loadPipes() {
            fetch('/api/get-pipes')
                .then(response => response.json())
                .then(data => {
                    // 清除旧管道
                    pipeLines.forEach(line => map.removeLayer(line));
                    pipeLines = [];

                    // 绘制管道
                    data.pipes.forEach(pipe => {
                        const startNode = existingNodes.find(n => n.node_id === pipe.start_node_id);
                        const endNode = existingNodes.find(n => n.node_id === pipe.end_node_id);

                        if (startNode && endNode) {
                            // Leaflet 期望 (纬度, 经度) -> (location_x, location_y)
                            const line = L.polyline([
                                [startNode.location_x, startNode.location_y],
                                [endNode.location_x, endNode.location_y]
                            ], {
                                color: pipe.status === '正常' ? 'blue' : 'gray',
                                weight: 3,
                                opacity: 0.7
                            }).addTo(map);

                          const distance = map.distance(
    [startNode.location_y, startNode.location_x],
    [endNode.location_y, endNode.location_x]
);

const pipePopupContent = `
    <div style="min-width: 250px;">
        <h4 style="margin: 0 0 10px 0; color: #1E88E5; border-bottom: 2px solid #e9ecef; padding-bottom: 5px;">
            🔧 ${pipe.pipe_id}
        </h4>
        <table style="width: 100%; font-size: 13px;">
            <tr><td style="padding: 3px; color: #666;"><b>起点:</b></td><td style="padding: 3px;">${pipe.start_node_id}</td></tr>
            <tr><td style="padding: 3px; color: #666;"><b>终点:</b></td><td style="padding: 3px;">${pipe.end_node_id}</td></tr>
            <tr><td style="padding: 3px; color: #666;"><b>管径:</b></td><td style="padding: 3px;">${pipe.diameter} m</td></tr>
            <tr><td style="padding: 3px; color: #666;"><b>状态:</b></td><td style="padding: 3px;"><span style="background: ${pipe.status === 'Open' ? '#4CAF50' : '#9E9E9E'}; color: white; padding: 2px 8px; border-radius: 3px;">${pipe.status}</span></td></tr>
            <tr><td style="padding: 3px; color: #666;"><b>长度:</b></td><td style="padding: 3px;">${distance.toFixed(2)} m</td></tr>
            <tr><td style="padding: 3px; color: #666;"><b>起点坐标:</b></td><td style="padding: 3px;">${startNode.location_y.toFixed(6)}, ${startNode.location_x.toFixed(6)}</td></tr>
            <tr><td style="padding: 3px; color: #666;"><b>终点坐标:</b></td><td style="padding: 3px;">${endNode.location_y.toFixed(6)}, ${endNode.location_x.toFixed(6)}</td></tr>
        </table>
    </div>
`;

line.bindPopup(pipePopupContent, {
    maxWidth: 350
});

// 添加点击事件提示
line.on('click', function() {
    updateStatus(`🔍 查看管道: ${pipe.pipe_id} (${pipe.start_node_id} → ${pipe.end_node_id})`, 'info');
});

                            pipeLines.push(line);
                        }
                    });
                });
        }

        // 缩放到节点
        function zoomToNode(lat, lng) {
            map.setView([lat, lng], 17);
        }

        // 更新状态
        function updateStatus(message, type) {
            const statusBox = document.getElementById('statusMsg');
            statusBox.textContent = message;
            statusBox.className = 'status-box';
            if (type) statusBox.classList.add(type);
        }

        // 页面加载完成后加载节点
        window.onload = function() {
            loadExistingNodes();
        };
    </script>
</body>
</html>'''


@app.route('/api/add-node', methods=['POST'])
def add_node():
    """添加节点到数据库"""
    try:
        data = request.json
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()

        # 注意：这里假设前端发送过来的 location_x 是经度 (X)，location_y 是纬度 (Y)
        # 与前端 input 字段 (locLat=纬度, locLng=经度) 的命名约定匹配
        c.execute('''INSERT INTO building_nodes 
                     (Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (data['node_id'], data['node_name'], data['node_type'],
                   data['level'], data['location_x'], data['location_y']))

        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/add-pipe', methods=['POST'])
def add_pipe():
    """添加管道到数据库"""
    try:
        data = request.json
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()

        c.execute('''INSERT INTO pipes 
                     (Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status)
                     VALUES (?, ?, ?, ?, ?)''',
                  (data['pipe_id'], data['start_node_id'], data['end_node_id'],
                   data['diameter'], data['status']))

        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/get-nodes', methods=['GET'])
def get_nodes():
    """获取所有节点"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('SELECT Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y FROM building_nodes')
        rows = c.fetchall()
        conn.close()

        nodes = []
        for row in rows:
            nodes.append({
                'node_id': row[0],
                'node_name': row[1],
                'node_type': row[2],
                'level': row[3],
                # ----------------------------------------------------
                # **修改点：在这里将 Location_X (经度) 和 Location_Y (纬度) 对调赋值**
                # 确保传给前端的 'location_x' 是纬度 (Y)，'location_y' 是经度 (X)
                'location_x': row[5],  # 数据库的 Location_Y (纬度) 赋值给 location_x
                'location_y': row[4]   # 数据库的 Location_X (经度) 赋值给 location_y
                # ----------------------------------------------------
            })

        return jsonify({'nodes': nodes})
    except Exception as e:
        return jsonify({'nodes': [], 'error': str(e)})


@app.route('/api/get-pipes', methods=['GET'])
def get_pipes():
    """获取所有管道"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('SELECT Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status FROM pipes')
        rows = c.fetchall()
        conn.close()

        pipes = []
        for row in rows:
            pipes.append({
                'pipe_id': row[0],
                'start_node_id': row[1],
                'end_node_id': row[2],
                'diameter': row[3],
                'status': row[4]
            })

        return jsonify({'pipes': pipes})
    except Exception as e:
        return jsonify({'pipes': [], 'error': str(e)})


if __name__ == '__main__':
    print("🚀 启动地图标注系统 (OpenStreetMap)...")
    print("🌐 访问 http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)