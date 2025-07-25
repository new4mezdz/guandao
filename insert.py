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

nodes = []
pos = {}
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

# 插入 building_nodes
c.executemany("""
INSERT INTO building_nodes
  (Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y)
VALUES (?,      ?,         ?,         ?,     ?,           ?)
""", nodes)
print(f"✅ 已插入 {len(nodes)} 个节点")

# —— 先计算每个节点到最近 A 级源的距离 —— 
# 找出所有 A 级源的坐标
A_coords = [pos[nid] for nid, *_ in nodes if nid.startswith("N00") and nid in pos and any(n[0]==nid and n[3]=="A" for n in nodes)]
dist_to_source = {}
for nid, *_ in nodes:
    dist_to_source[nid] = min(
        math.hypot(pos[nid][0] - ax, pos[nid][1] - ay)
        for ax, ay in A_coords
    )

# —— 生成管道 & 阀门（每节点指向 k 个最近邻，但方向由上游→下游） —— 
pipes = []
valves = []
pipe_count = 0

for u in pos:
    # 计算到所有其他节点的距离并取 k 最近
    dists = [(math.hypot(pos[u][0]-pos[v][0], pos[u][1]-pos[v][1]), v)
             for v in pos if v != u]
    nearest = [v for _, v in sorted(dists, key=lambda x: x[0])[:k]]
    for v in nearest:
        # 确定方向：dist_to_source 小的为上游
        if dist_to_source[u] <= dist_to_source[v]:
            start, end = u, v
        else:
            start, end = v, u

        pid = f"P{pipe_count:04d}"
        diameter = random.choice([100,150,200,300,500])
        pipes.append((pid, start, end, diameter, "正常"))
        valves.append((f"V{pipe_count:04d}", pid, "正常"))
        pipe_count += 1

# 插入 pipes 和 valves
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
print(f"✅ 已插入 {len(pipes)} 条管道，{len(valves)} 个阀门")

# —— 提交 & 关闭 —— 
conn.commit()
conn.close()
print("🎉 50节点网络已按物理流向写入 my_database.db！")
