import sqlite3
import networkx as nx

def isolate_leakage(leak_node_pairs, leak_type, fail_valve_id=None):
    """
    供水隔离算法（支持多漏损 + 超级源/汇 + 等级惩罚 + 业务规则判断）
    输入:
        leak_node_pairs: list of tuple, 漏损节点对列表 [(start, end), ...]
        leak_type: "普通漏损" / "爆管"
        fail_valve_id: 临时失效阀门ID（或 None/无）
    输出:
        dict 包含 need_close_valves, lost_valves, isolatable, cut_edges, leak_type, recommendation
    """
    # 连接数据库
    conn = sqlite3.connect("my_database.db")
    c = conn.cursor()
    c.execute("SELECT Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y FROM building_nodes")
    nodes = c.fetchall()
    c.execute("SELECT Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status FROM pipes")
    pipes = c.fetchall()
    c.execute("SELECT Valve_ID, Controlled_Pipe_ID, Status FROM valves")
    valves = c.fetchall()
    conn.close()
    node_level_map = {n[0]: n[3] for n in nodes}
    # 失效阀门处理
    if fail_valve_id and fail_valve_id.lower() != '无':
        valves = [(v[0], v[1], '失效') if v[0] == fail_valve_id else v for v in valves]
    lost_valves = [v[0] for v in valves if v[2] != "正常"]
    # 1. 爆管：无条件隔离
    if leak_type == "爆管":
        leak_pair = leak_node_pairs[0] if isinstance(leak_node_pairs, list) else leak_node_pairs
        leak_pipe_list = [p for p in pipes if (p[1], p[2]) == tuple(leak_pair)]
        if not leak_pipe_list:
            return {
                "need_close_valves": [],
                "lost_valves": lost_valves,
                "isolatable": False,
                "cut_edges": [],
                "leak_type": leak_type,
                "recommendation": f"节点对 {leak_pair} 不存在对应管道，无法隔离"
            }
        leak_pipe = leak_pipe_list[0]
        leak_pipe_id = leak_pipe[0]
        valve_ids = [v[0] for v in valves if v[1] == leak_pipe_id and v[2] == "正常"]
        return {
            "need_close_valves": valve_ids[:1],
            "lost_valves": lost_valves,
            "isolatable": True,
            "cut_edges": [],
            "leak_type": leak_type,
            "recommendation": "爆管紧急隔离，相关用户（包括高等级用户）将临时断水，请立即抢修"
        }
    # 2. 管道漏损业务规则判断
    for (start, end) in leak_node_pairs:
        for node in [start, end]:
            level = node_level_map.get(node, 'C')
            # 查输入管道数（不含本管道）
            input_pipes = [p for p in pipes if p[2] == node and (p[1], p[2]) != (start, end)]
            if level == 'A':
                if len(input_pipes) == 0:
                    return {
                        "need_close_valves": [],
                        "lost_valves": lost_valves,
                        "isolatable": False,
                        "cut_edges": [],
                        "leak_type": leak_type,
                        "recommendation": f"A级建筑{node}仅有一条供水，禁止隔离，必须保障供水"
                    }
            elif level == 'B':
                if len(input_pipes) == 0:
                    return {
                        "need_close_valves": [],
                        "lost_valves": lost_valves,
                        "isolatable": False,
                        "cut_edges": [],
                        "leak_type": leak_type,
                        "recommendation": f"B级建筑{node}仅有一条供水，不建议隔离，建议优先抢修"
                    }
    # 3. 普通漏损/节点漏损，继续原有最小割隔离
    G = nx.DiGraph()
    for node in nodes:
        node_id = node[0]
        G.add_node(node_id)
    for pipe in pipes:
        pipe_id, start, end, diameter, status = pipe
        end_level = node_level_map.get(end, 'C')
        capacity = diameter ** 2
        if end_level == 'A':
            capacity *= 10000
        elif end_level == 'B':
            capacity *= 100
        if (start, end) in leak_node_pairs:
            capacity = 10
        G.add_edge(start, end,
                   pipe_id=pipe_id,
                   diameter=diameter,
                   status=status,
                   capacity=capacity)
    for valve in valves:
        valve_id, controlled_pipe_id, status = valve
        for u, v, data in G.edges(data=True):
            if data['pipe_id'] == controlled_pipe_id:
                if status != "正常":
                    data['capacity'] = float('inf')
                data['valve_id'] = valve_id
    G.add_node('super_source')
    source_nodes = [n[0] for n in nodes if n[3] == 'A' and n[2] == '水厂']
    for src in source_nodes:
        G.add_edge('super_source', src, capacity=float('inf'))
    G.add_node('super_sink')
    for leak_pair in leak_node_pairs:
        sink = leak_pair[1]
        G.add_edge(sink, 'super_sink', capacity=float('inf'))
    cut_value, partition = nx.minimum_cut(G, 'super_source', 'super_sink', capacity='capacity')
    reachable, non_reachable = partition
    cut_edges = []
    need_close_valves = []
    for u in reachable:
        for v in G[u]:
            if v in non_reachable and v != 'super_sink':
                cut_edges.append((u, v))
                valve_id = G[u][v].get('valve_id')
                if valve_id:
                    need_close_valves.append(valve_id)
    isolatable = cut_value < float('inf')
    recommendation = "隔离成功" if isolatable else "无法隔离，需施工切断"
    return {
        "need_close_valves": list(set(need_close_valves)),
        "lost_valves": lost_valves,
        "isolatable": isolatable,
        "cut_edges": cut_edges,
        "leak_type": leak_type,
        "recommendation": recommendation
    }

# ✅ **测试调用示例**
if __name__ == "__main__":
    print("【🔍 测试示例】")
    leak_node_pairs_input = input("请输入漏损节点对（格式A,B;C,D）：").strip()
    leak_node_pairs = [tuple(pair.strip().split(',')) for pair in leak_node_pairs_input.split(';') if pair.strip()]
    leak_type = input("请输入泄漏类型（普通漏损/爆管）：").strip()
    fail_valve_id = input("请输入失效阀门ID（或无）：").strip()
    result = isolate_leakage(leak_node_pairs, leak_type, fail_valve_id)
    print("\n🔷 测试结果")
    print("➡️ 需要关闭的阀门:", result.get("need_close_valves"))
    print("➡️ 失效阀门:", result.get("lost_valves"))
    print("➡️ 是否可隔离:", result.get("isolatable"))
    print("➡️ cut 边:", result.get("cut_edges"))
    print("➡️ 建议:", result.get("recommendation"))
