import sqlite3
import random
import math

# —— 配置 —— 
random.seed(42)
total_nodes = 50
k = 3  # 最近邻数

# —— 连接数据库 —— 
conn = sqlite3.connect("my_database.db")
c = conn.cursor()

# —— 清空旧数据 —— 
c.execute("DELETE FROM valves")
c.execute("DELETE FROM pipes")
c.execute("DELETE FROM building_nodes")
print("✅ 已清空旧的 building_nodes, pipes, valves 数据")

# —— 生成节点 & 随机位置 —— 
num_A = 2
num_B = int(0.10 * total_nodes)  # 5
num_C = total_nodes - num_A - num_B  # 43

nodes = []    # 存 (Node_ID, Name, Type, Level, x, y)
pos = {}      # 存 {Node_ID: (x, y)}
idx = 0

# A 级源
for i in range(num_A):
    nid = f"N{idx:03d}"
    x, y = random.uniform(0,20), random.uniform(0,20)
    nodes.append((nid, f"A级源{i+1}", "水厂", "A", x, y))
    pos[nid] = (x, y)
    idx += 1

# B 级用户
for i in range(num_B):
    nid = f"N{idx:03d}"
    x, y = random.uniform(0,20), random.uniform(0,20)
    nodes.append((nid, f"B级用户{i+1}", "学校", "B", x, y))
    pos[nid] = (x, y)
    idx += 1

# C 级用户
for i in range(num_C):
    nid = f"N{idx:03d}"
    x, y = random.uniform(0,20), random.uniform(0,20)
    nodes.append((nid, f"C级用户{i+1}", "住宅", "C", x, y))
    pos[nid] = (x, y)
    idx += 1

# 批量插入节点
c.executemany("""
INSERT INTO building_nodes
  (Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y)
VALUES (?,      ?,         ?,         ?,     ?,           ?)
""", nodes)
print(f"✅ 已插入 {len(nodes)} 个节点")

# —— 计算每个节点到最近 A 级源的距离 —— 
A_coords = [pos[nid] for nid,_,_,lev,_,_ in nodes if lev == 'A']
dist_to_source = {
    nid: min(math.hypot(pos[nid][0]-ax, pos[nid][1]-ay) for ax,ay in A_coords)
    for nid,_,_,_,_,_ in nodes
}

# —— 生成初始 pipes & valves（k 最近邻 + 保证方向自上游到下游） —— 
pipes = []   # 存 (Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status)
valves = []  # 存 (Valve_ID, Controlled_Pipe_ID, Status)
pipe_count = 0

for u in pos:
    # 找出 u 到其他节点的距离并取 k 最近
    dists = [(math.hypot(pos[u][0]-pos[v][0], pos[u][1]-pos[v][1]), v)
             for v in pos if v != u]
    nearest = [v for _, v in sorted(dists, key=lambda x: x[0])[:k]]
    for v in nearest:
        # 根据 dist_to_source 决定方向：小的为上游（Start），大的为下游（End）
        if dist_to_source[u] <= dist_to_source[v]:
            start, end = u, v
        else:
            start, end = v, u

        pid = f"P{pipe_count:04d}"
        dia = random.choice([100, 150, 200, 300, 500])
        pipes.append((pid, start, end, dia, "正常"))
        valves.append((f"V{pipe_count:04d}", pid, "正常"))
        pipe_count += 1

# —— 检查可达性 & 补充不连通节点 —— 
# 构建邻接表
adj = {}
for _, s, e, _, _ in pipes:
    adj.setdefault(s, []).append(e)

# 从所有 A 级源开始做 BFS
reachable = set(nid for nid,_,_,lev,_,_ in nodes if lev == 'A')
queue = list(reachable)
while queue:
    cur = queue.pop(0)
    for nbr in adj.get(cur, []):
        if nbr not in reachable:
            reachable.add(nbr)
            queue.append(nbr)

# 找出不可达节点
all_ids = set(pos.keys())
unreachable = all_ids - reachable
if unreachable:
    print(f"⚠️ 以下节点最初不可达，将自动补连：{sorted(unreachable)}")
for nid in unreachable:
    # 找一个最近的可达节点作为上游
    cand = min(reachable,
               key=lambda x: math.hypot(pos[nid][0]-pos[x][0],
                                       pos[nid][1]-pos[x][1]))
    pid = f"P{pipe_count:04d}"
    dia = random.choice([100, 150, 200, 300, 500])
    pipes.append((pid, cand, nid, dia, "正常"))
    valves.append((f"V{pipe_count:04d}", pid, "正常"))
    pipe_count += 1
    print(f"🔗 补充管道 {cand} -> {nid}")

# —— 批量插入 pipes & valves —— 
c.executemany("""
INSERT INTO pipes
  (Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status)
VALUES (?,       ?,             ?,           ?,        ?)
""", pipes)
c.executemany("""
INSERT INTO valves
  (Valve_ID, Controlled_Pipe_ID, Status)
VALUES (?,       ?,                 ?)
""", valves)
print(f"✅ 已插入总共 {len(pipes)} 条管道，{len(valves)} 个阀门")

# —— 提交 & 关闭 —— 
conn.commit()
conn.close()
print("🎉 50节点网络（保证全网可达）已写入 my_database.db！")
