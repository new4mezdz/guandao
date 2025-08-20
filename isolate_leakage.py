import sqlite3
import networkx as nx


def integrated_water_isolation(leak_target, leak_type, fail_valve_id=None):
    """
    集成的供水隔离算法
    根据不同的漏损类型采用不同的处理策略

    参数:
        leak_target: 漏损目标（节点ID或管道ID）
        leak_type: "节点漏损", "普通漏损", "爆管"
        fail_valve_id: 失效阀门ID（可选）

    返回:
        dict 包含详细的隔离结果
    """
    print(f"🚰 启动集成隔离算法: {leak_type} - {leak_target}")

    if leak_type == "节点漏损":
        return handle_node_leakage(leak_target, fail_valve_id)
    elif leak_type in ["普通漏损", "爆管"]:
        return handle_pipe_leakage(leak_target, leak_type, fail_valve_id)
    else:
        return {
            "success": False,
            "error": f"未知的漏损类型: {leak_type}",
            "recommendation": "请选择正确的漏损类型：节点漏损、普通漏损或爆管"
        }


def handle_pipe_leakage(leak_pipe_id, leak_type, fail_valve_id=None):
    """
    处理管道漏损（普通漏损和爆管）
    实现改进的分层处理策略
    """
    # 获取基础数据
    conn = sqlite3.connect("my_database.db")
    c = conn.cursor()

    c.execute("SELECT Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y FROM building_nodes")
    nodes = c.fetchall()

    c.execute("SELECT Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status FROM pipes")
    pipes = c.fetchall()

    c.execute("SELECT Valve_ID, Controlled_Pipe_ID, Status FROM valves")
    valves = c.fetchall()

    conn.close()

    # 创建映射表
    pipe_map = {p[0]: p for p in pipes}
    valve_map = {v[1]: v for v in valves}  # pipe_id -> valve

    # 验证管道存在
    if leak_pipe_id not in pipe_map:
        return create_error_result(f"管道 {leak_pipe_id} 不存在")

    leak_pipe = pipe_map[leak_pipe_id]
    leak_start, leak_end = leak_pipe[1], leak_pipe[2]

    # 收集失效阀门
    lost_valves = collect_lost_valves(valves, fail_valve_id)

    print(f"🔍 分析管道: {leak_pipe_id} ({leak_start} -> {leak_end})")

    # 策略1：直接阀门控制
    direct_result = try_direct_valve_control(leak_pipe_id, leak_type, valve_map, lost_valves)
    if direct_result["success"]:
        return direct_result

    # 策略2：上游阀门控制
    upstream_result = try_upstream_valve_control(
        leak_pipe_id, leak_type, pipes, valve_map, lost_valves
    )
    if upstream_result["success"]:
        return upstream_result

    # 策略3：复杂隔离策略
    complex_result = try_complex_isolation(
        leak_pipe_id, leak_type, leak_start, pipes, valves, nodes, lost_valves
    )
    return complex_result


def try_direct_valve_control(leak_pipe_id, leak_type, valve_map, lost_valves):
    """策略1：尝试直接关闭管道阀门"""
    pipe_valve = valve_map.get(leak_pipe_id)

    if pipe_valve and pipe_valve[2] == "正常" and pipe_valve[0] not in lost_valves:
        print(f"✅ 找到可用的直接阀门: {pipe_valve[0]}")

        if leak_type == "爆管":
            recommendation = f"🚨 爆管紧急隔离：立即关闭阀门 {pipe_valve[0]}，已通知抢修部门紧急处理"
            priority = "紧急"
        else:
            recommendation = f"✅ 普通漏损直接隔离：关闭管道 {leak_pipe_id} 的阀门 {pipe_valve[0]}"
            priority = "正常"

        return {
            "success": True,
            "isolation_method": "直接阀门控制",
            "leak_target": leak_pipe_id,
            "leak_type": leak_type,
            "priority": priority,
            "need_close_valves": [pipe_valve[0]],
            "lost_valves": lost_valves,
            "isolatable": True,
            "affected_pipes": [leak_pipe_id],
            "affected_pipes_count": 1,
            "recommendation": recommendation,
            "emergency_notification": leak_type == "爆管"
        }

    print(f"❌ 直接阀门不可用: {pipe_valve[0] if pipe_valve else '无阀门'}")
    return {"success": False}


def try_upstream_valve_control(leak_pipe_id, leak_type, pipes, valve_map, lost_valves):
    """策略2：尝试上游阀门控制"""
    leak_pipe = next(p for p in pipes if p[0] == leak_pipe_id)
    leak_start = leak_pipe[1]

    # 查找上游管道
    upstream_pipes = [p for p in pipes if p[2] == leak_start]

    if len(upstream_pipes) == 0:
        print("❌ 没有上游管道（源头管道）")
        return {"success": False, "reason": "源头管道"}

    elif len(upstream_pipes) == 1:
        # 直线型结构
        upstream_pipe = upstream_pipes[0]
        upstream_valve = valve_map.get(upstream_pipe[0])

        if upstream_valve and upstream_valve[2] == "正常" and upstream_valve[0] not in lost_valves:
            print(f"✅ 找到可用的上游阀门: {upstream_valve[0]}")

            if leak_type == "爆管":
                recommendation = f"🚨 爆管上游隔离：关闭上游阀门 {upstream_valve[0]}，已通知抢修部门"
                priority = "紧急"
            else:
                recommendation = f"⬆️ 上游隔离：关闭上游管道 {upstream_pipe[0]} 的阀门 {upstream_valve[0]}"
                priority = "正常"

            return {
                "success": True,
                "isolation_method": "上游阀门控制",
                "leak_target": leak_pipe_id,
                "leak_type": leak_type,
                "priority": priority,
                "need_close_valves": [upstream_valve[0]],
                "lost_valves": lost_valves,
                "isolatable": True,
                "affected_pipes": [upstream_pipe[0], leak_pipe_id],
                "affected_pipes_count": 2,
                "recommendation": recommendation,
                "emergency_notification": leak_type == "爆管"
            }
        else:
            # 递归向上寻找
            print(f"🔄 上游阀门不可用，递归寻找: {upstream_pipe[0]}")
            return try_upstream_valve_control(upstream_pipe[0], leak_type, pipes, valve_map, lost_valves)

    else:
        # 多输入型结构
        print(f"🌐 发现多输入型结构，上游管道: {[p[0] for p in upstream_pipes]}")
        return {"success": False, "reason": "多输入型", "upstream_pipes": upstream_pipes}


def try_complex_isolation(leak_pipe_id, leak_type, leak_start, pipes, valves, nodes, lost_valves):
    """策略3：复杂隔离策略"""
    if leak_type == "爆管":
        # 爆管：尝试关闭所有可用上游阀门
        return handle_burst_pipe_complex(leak_pipe_id, leak_start, pipes, valves, lost_valves)
    else:
        # 普通漏损：转为节点漏损处理
        return handle_as_node_leakage_advanced(leak_start, pipes, valves, nodes, lost_valves)


def handle_burst_pipe_complex(leak_pipe_id, leak_start, pipes, valves, lost_valves):
    """处理复杂的爆管情况"""
    print("🚨 爆管复杂处理：尝试关闭所有可用上游阀门")

    # 找到所有上游管道
    upstream_pipes = [p for p in pipes if p[2] == leak_start]
    valve_map = {v[1]: v for v in valves}

    available_upstream_valves = []
    affected_pipes = [leak_pipe_id]

    for upstream_pipe in upstream_pipes:
        upstream_valve = valve_map.get(upstream_pipe[0])
        if upstream_valve and upstream_valve[2] == "正常" and upstream_valve[0] not in lost_valves:
            available_upstream_valves.append(upstream_valve[0])
            affected_pipes.append(upstream_pipe[0])

    if available_upstream_valves:
        print(f"✅ 爆管多上游隔离，关闭阀门: {available_upstream_valves}")
        return {
            "success": True,
            "isolation_method": "爆管多上游隔离",
            "leak_target": leak_pipe_id,
            "leak_type": "爆管",
            "priority": "紧急",
            "need_close_valves": available_upstream_valves,
            "lost_valves": lost_valves,
            "isolatable": True,
            "affected_pipes": affected_pipes,
            "affected_pipes_count": len(affected_pipes),
            "recommendation": f"🚨 爆管紧急情况：关闭所有可用上游阀门 {available_upstream_valves}，已通知抢修部门立即处理",
            "emergency_notification": True
        }
    else:
        print("❌ 爆管且所有上游阀门都不可用")
        return {
            "success": False,
            "isolation_method": "无法隔离",
            "leak_target": leak_pipe_id,
            "leak_type": "爆管",
            "priority": "紧急",
            "need_close_valves": [],
            "lost_valves": lost_valves,
            "isolatable": False,
            "affected_pipes": [leak_pipe_id],
            "affected_pipes_count": 1,
            "recommendation": "🚨 爆管紧急情况：所有阀门失效，需立即联系水厂断供并安排紧急抢修",
            "emergency_notification": True,
            "manual_intervention_required": True
        }


def handle_as_node_leakage_advanced(leak_node, pipes, valves, nodes, lost_valves):
    """将复杂管道漏损转为高级节点漏损处理"""
    print(f"🔄 转换为节点漏损算法处理节点: {leak_node}")

    # 构建网络图
    G = nx.DiGraph()
    node_level_map = {n[0]: n[3] for n in nodes}

    # 添加节点
    for node in nodes:
        G.add_node(node[0])

    # 创建临时图用于距离计算
    temp_graph = nx.Graph()
    for pipe in pipes:
        temp_graph.add_edge(pipe[1], pipe[2])

    # 添加边并设置容量
    for pipe in pipes:
        pipe_id, start, end, diameter, status = pipe

        # 基础容量
        base_capacity = diameter ** 2

        # 根据终点等级设置权重
        end_level = node_level_map.get(end, 'C')
        if end_level == 'A':
            level_multiplier = 10000
        elif end_level == 'B':
            level_multiplier = 100
        else:
            level_multiplier = 1

        capacity = base_capacity * level_multiplier

        # 计算距离因子
        try:
            hop_distance = nx.shortest_path_length(temp_graph, source=leak_node, target=start)
            distance_factor =  (1.0 + hop_distance)**3
            capacity = capacity * distance_factor
        except:
            pass  # 如果无法计算距离，使用原始容量

        G.add_edge(start, end, pipe_id=pipe_id, capacity=capacity)

    # 处理阀门
    valve_map = {v[1]: v for v in valves}
    for pipe_id, valve in valve_map.items():
        valve_id, controlled_pipe_id, valve_status = valve

        for u, v, data in G.edges(data=True):
            if data['pipe_id'] == controlled_pipe_id:
                if valve_status != "正常" or valve_id in lost_valves:
                    data['capacity'] = float('inf')  # 失效阀门
                    data['valve_status'] = 'failed'
                else:
                    data['valve_id'] = valve_id
                    data['valve_status'] = 'normal'

    # 设置源点和汇点
    G.add_node('super_source')
    source_nodes = [n[0] for n in nodes if n[3] == 'A' and n[2] == '水厂']
    if not source_nodes:
        source_nodes = [n[0] for n in nodes if n[3] == 'A']

    for src in source_nodes:
        G.add_edge('super_source', src, capacity=float('inf'))

    G.add_node('super_sink')
    G.add_edge(leak_node, 'super_sink', capacity=float('inf'))

    # 执行最小割
    try:
        cut_value, partition = nx.minimum_cut(G, 'super_source', 'super_sink', capacity='capacity')
        reachable, non_reachable = partition

        need_close_valves = []
        cut_edges = []
        cut_pipes = []

        for u in reachable:
            for v in G[u]:
                if v in non_reachable and v != 'super_sink':
                    edge_data = G[u][v]
                    cut_edges.append((u, v))
                    cut_pipes.append(edge_data['pipe_id'])

                    valve_id = edge_data.get('valve_id')
                    if valve_id and edge_data.get('valve_status') == 'normal':
                        need_close_valves.append(valve_id)

        need_close_valves = list(set(need_close_valves))
        isolatable = cut_value < float('inf')

        # 分析影响的建筑等级
        affected_levels = set()
        for u, v in cut_edges:
            if v != 'super_sink':
                level = node_level_map.get(v, 'C')
                affected_levels.add(level)

        # 生成建议
        if not isolatable:
            recommendation = f"❌ 节点 {leak_node} 无法完全隔离，存在无法控制的路径"
            priority = "高"
        elif 'A' in affected_levels:
            recommendation = f"⚠️ 隔离将影响A级建筑供水，需要紧急协调备用供水方案"
            priority = "高"
        elif 'B' in affected_levels:
            recommendation = f"⚠️ 隔离将影响B级建筑供水，建议提前通知相关部门"
            priority = "中"
        else:
            recommendation = f"✅ 隔离影响范围主要为C级建筑，可以执行隔离操作"
            priority = "正常"

        return {
            "success": True,
            "isolation_method": "节点漏损最小割算法",
            "leak_target": leak_node,
            "leak_type": "转换的节点漏损",
            "priority": priority,
            "need_close_valves": need_close_valves,
            "lost_valves": lost_valves,
            "isolatable": isolatable,
            "cut_edges": cut_edges,
            "affected_pipes": cut_pipes,
            "affected_pipes_count": len(cut_pipes),
            "affected_building_levels": list(affected_levels),
            "recommendation": recommendation,
            "emergency_notification": 'A' in affected_levels
        }

    except Exception as e:
        return create_error_result(f"节点漏损算法执行失败: {str(e)}")


def handle_node_leakage(leak_node, fail_valve_id=None):
    """处理节点漏损"""
    print(f"🔵 处理节点漏损: {leak_node}")

    # 获取数据
    conn = sqlite3.connect("my_database.db")
    c = conn.cursor()

    c.execute("SELECT Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y FROM building_nodes")
    nodes = c.fetchall()

    c.execute("SELECT Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status FROM pipes")
    pipes = c.fetchall()

    c.execute("SELECT Valve_ID, Controlled_Pipe_ID, Status FROM valves")
    valves = c.fetchall()

    conn.close()

    # 验证节点存在
    node_map = {n[0]: n for n in nodes}
    if leak_node not in node_map:
        return create_error_result(f"节点 {leak_node} 不存在")

    lost_valves = collect_lost_valves(valves, fail_valve_id)

    # 直接调用高级节点漏损处理
    return handle_as_node_leakage_advanced(leak_node, pipes, valves, nodes, lost_valves)


def collect_lost_valves(valves, fail_valve_id):
    """收集所有失效阀门"""
    lost_valves = []

    if fail_valve_id:
        lost_valves.append(fail_valve_id)

    for valve in valves:
        if valve[2] != "正常":
            lost_valves.append(valve[0])

    return list(set(lost_valves))


def create_error_result(error_message):
    """创建错误结果"""
    return {
        "success": False,
        "error": error_message,
        "need_close_valves": [],
        "lost_valves": [],
        "isolatable": False,
        "recommendation": f"处理失败: {error_message}"
    }


# 测试和演示函数
def test_integrated_algorithm():
    """测试集成隔离算法"""
    print("🧪 测试集成供水隔离算法")
    print("=" * 60)

    test_cases = [
        {
            "name": "节点漏损测试",
            "target": "N002",
            "type": "节点漏损",
            "fail_valve": None
        },
        {
            "name": "普通管道漏损（直接阀门）",
            "target": "P0001",
            "type": "普通漏损",
            "fail_valve": None
        },
        {
            "name": "普通管道漏损（阀门失效）",
            "target": "P0002",
            "type": "普通漏损",
            "fail_valve": "V0002"
        },
        {
            "name": "爆管（正常阀门）",
            "target": "P0003",
            "type": "爆管",
            "fail_valve": None
        },
        {
            "name": "爆管（阀门失效）",
            "target": "P0004",
            "type": "爆管",
            "fail_valve": "V0004"
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n{'=' * 20} 测试用例 {i}: {case['name']} {'=' * 20}")
        print(f"目标: {case['target']}, 类型: {case['type']}, 失效阀门: {case['fail_valve']}")

        try:
            result = integrated_water_isolation(
                case["target"],
                case["type"],
                case["fail_valve"]
            )

            print("\n📊 测试结果:")
            print(f"   ✅ 成功: {result.get('success', False)}")
            print(f"   🔧 隔离方法: {result.get('isolation_method', 'N/A')}")
            print(f"   🚦 优先级: {result.get('priority', 'N/A')}")
            print(f"   🔐 需关闭阀门: {result.get('need_close_valves', [])}")
            print(f"   ❌ 失效阀门: {result.get('lost_valves', [])}")
            print(f"   📍 可隔离: {result.get('isolatable', False)}")
            print(f"   📋 影响管道数: {result.get('affected_pipes_count', 0)}")

            if result.get('emergency_notification'):
                print(f"   🚨 紧急通知: 是")

            print(f"   💡 建议: {result.get('recommendation', 'N/A')}")

            if result.get('manual_intervention_required'):
                print(f"   ⚠️  需要人工干预")

        except Exception as e:
            print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    test_integrated_algorithm()