import sqlite3
import networkx as nx

def isolate_leakage(leak_pipe_ids, leak_type, fail_valve_id=None):
    """
    供水隔离算法（支持多漏损 + 超级源/汇 + 等级惩罚）
    输入:
        leak_pipe_ids: list, 漏损管道ID列表
        leak_type: "普通漏损" / "爆管"
        fail_valve_id: 临时失效阀门ID（或 None/无）
    输出:
        dict 包含 need_close_valves, lost_valves, isolatable, cut_edges, leak_type, recommendation
    """

    # 连接数据库
    conn = sqlite3.connect("my_database.db")
    c = conn.cursor()

    # 读取 building_nodes
    c.execute("SELECT Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y FROM building_nodes")
    nodes = c.fetchall()

    # 读取 pipes
    c.execute("SELECT Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status FROM pipes")
    pipes = c.fetchall()

    # 读取 valves
    c.execute("SELECT Valve_ID, Controlled_Pipe_ID, Status FROM valves")
    valves = c.fetchall()
    conn.close()

    # 🔧 临时将 fail_valve_id 状态改为失效
    if fail_valve_id and fail_valve_id.lower() != '无':
        valves = [(v[0], v[1], '失效') if v[0] == fail_valve_id else v for v in valves]

    # 初始化 lost_valves
    lost_valves = [v[0] for v in valves if v[2] != "正常"]

    # 🔷 爆管场景（保持单 leak_pipe_id 输入）
    if leak_type == "爆管":
        leak_pipe_id = leak_pipe_ids[0] if isinstance(leak_pipe_ids, list) else leak_pipe_ids
        leak_pipe_list = [p for p in pipes if p[0] == leak_pipe_id]

        if not leak_pipe_list:
            return {
                "need_close_valves": [],
                "lost_valves": lost_valves,
                "isolatable": False,
                "cut_edges": [],
                "leak_type": leak_type,
                "recommendation": f"管道 {leak_pipe_id} 不存在，无法隔离"
            }

        leak_pipe = leak_pipe_list[0]

        valve_ids = [v[0] for v in valves if v[1] == leak_pipe_id and v[2] == "正常"]

        if valve_ids:
            return {
                "need_close_valves": valve_ids[:1],
                "lost_valves": lost_valves,
                "isolatable": True,
                "cut_edges": [],
                "leak_type": leak_type,
                "recommendation": "关闭上游阀门完成隔离"
            }
        else:
            neighbor_valves = []
            start_node, end_node = leak_pipe[1], leak_pipe[2]

            for pipe in pipes:
                pid, s, e, dia, status = pipe
                if pid == leak_pipe_id:
                    continue
                if s in [start_node, end_node] or e in [start_node, end_node]:
                    v_ids = [v[0] for v in valves if v[1] == pid and v[2] == "正常"]
                    neighbor_valves.extend(v_ids)

            recommendation = "需人工切断" if not neighbor_valves else "建议同时关闭临近阀门，必要时施工切断"

            return {
                "need_close_valves": neighbor_valves,
                "lost_valves": lost_valves,
                "isolatable": False,
                "cut_edges": [],
                "leak_type": leak_type,
                "recommendation": recommendation
            }

    # 🔷 普通漏损场景（支持多漏损）
    elif leak_type == "普通漏损":
        G = nx.DiGraph()

        # 添加节点
        for node in nodes:
            node_id = node[0]
            G.add_node(node_id)

        # 添加边，计算 capacity 时引入等级惩罚
        for pipe in pipes:
            pipe_id, start, end, diameter, status = pipe

            # 获取 end_node 的等级
            end_level = next((n[3] for n in nodes if n[0]==end), 'C')

            # 计算基础 capacity
            capacity = diameter ** 2

            # 应用等级惩罚
            if end_level == 'A':
                capacity *= 10000
            elif end_level == 'B':
                capacity *= 100
            # C 级保持原值

            # 若为任何一个泄漏管道，则 capacity 设为最小
            if pipe_id in leak_pipe_ids:
                capacity = 10

            G.add_edge(start, end,
                       pipe_id=pipe_id,
                       diameter=diameter,
                       status=status,
                       capacity=capacity)

        # 阀门状态对 capacity 的影响
        for valve in valves:
            valve_id, controlled_pipe_id, status = valve
            for u, v, data in G.edges(data=True):
                if data['pipe_id'] == controlled_pipe_id:
                    if status != "正常":
                        data['capacity'] = float('inf')
                    data['valve_id'] = valve_id

        ### 🚀 添加超级源 ###
        G.add_node('super_source')
        # 🚀 动态获取所有源节点
        source_nodes = [n[0] for n in nodes if n[3] == 'A' and n[2] == '水厂']

        print("✅ 检测到源节点:", source_nodes)  # debug

        # 添加超级源边
        for src in source_nodes:
            G.add_edge('super_source', src, capacity=float('inf'))

        ### 🚀 添加超级汇 ###
        G.add_node('super_sink')
        for leak_pipe_id in leak_pipe_ids:
            leak_pipe_list = [p for p in pipes if p[0] == leak_pipe_id]
            if leak_pipe_list:
                sink = leak_pipe_list[0][2]
                G.add_edge(sink, 'super_sink', capacity=float('inf'))

        # 计算最小割（super_source → super_sink）
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

    # 🔷 无效 leak_type
    else:
        return {"error": "leak_type 无效"}


# ✅ **测试调用示例**
if __name__ == "__main__":
    print("【🔍 测试示例】")
    leak_pipe_ids_input = input("请输入泄漏管道ID（可输入多个，用英文逗号分隔）：").strip()
    leak_pipe_ids = [pid.strip() for pid in leak_pipe_ids_input.split(',')]

    leak_type = input("请输入泄漏类型（普通漏损/爆管）：").strip()
    fail_valve_id = input("请输入失效阀门ID（或无）：").strip()

    result = isolate_leakage(leak_pipe_ids, leak_type, fail_valve_id)

    print("\n🔷 测试结果")
    print("➡️ 需要关闭的阀门:", result.get("need_close_valves"))
    print("➡️ 失效阀门:", result.get("lost_valves"))
    print("➡️ 是否可隔离:", result.get("isolatable"))
    print("➡️ cut 边:", result.get("cut_edges"))
    print("➡️ 建议:", result.get("recommendation"))
