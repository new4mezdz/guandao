import sqlite3

# 连接数据库
conn = sqlite3.connect("my_database.db")
c = conn.cursor()

print("🔧 在现有数据库基础上添加新的网络结构...")

# =============== 网络1：简单s-t网络 ===============
print("\n📍 添加网络1：简单s-t网络")

# 添加节点（WP001作为水厂，其他节点用不同前缀避免冲突）
network1_nodes = [
    ("WP001", "水厂WP001", "水厂", "A", 20, 25),    # 源点
    ("S1", "节点S1", "住宅", "C", 25, 30),          # 节点1
    ("S2", "节点S2", "住宅", "C", 25, 20),          # 节点2
    ("ST", "汇点ST", "住宅", "C", 30, 25)           # 汇点
]

c.executemany("""
INSERT OR IGNORE INTO building_nodes
  (Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y)
VALUES (?,      ?,         ?,         ?,     ?,           ?)
""", network1_nodes)

# 添加管道（根据原图半径：WP001->S1(3), WP001->S2(2), S1->ST(3), S2->ST(2), S1->S2(1)）
network1_pipes = [
    ("PS001", "WP001", "S1", 600, "正常"),  # 半径3，直径600
    ("PS002", "WP001", "S2", 400, "正常"),  # 半径2，直径400
    ("PS003", "S1", "ST", 600, "正常"),     # 半径3，直径600
    ("PS004", "S2", "ST", 400, "正常"),     # 半径2，直径400
    ("PS005", "S1", "S2", 200, "正常")      # 半径1，直径200
]

c.executemany("""
INSERT OR IGNORE INTO pipes
  (Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status)
VALUES (?,       ?,             ?,           ?,        ?)
""", network1_pipes)

# 添加阀门
network1_valves = [
    ("VS001", "PS001", "正常"),
    ("VS002", "PS002", "正常"),
    ("VS003", "PS003", "正常"),
    ("VS004", "PS004", "正常"),
    ("VS005", "PS005", "正常")
]

c.executemany("""
INSERT OR IGNORE INTO valves
  (Valve_ID, Controlled_Pipe_ID, Status)
VALUES (?,       ?,                 ?)
""", network1_valves)

print("✅ 网络1添加完成：WP001 -> S1/S2 -> ST")

# =============== 网络2：菱形网络 ===============
print("\n📍 添加网络2：菱形网络")

# 添加节点
network2_nodes = [
    ("WP002", "水厂WP002", "水厂", "A", 40, 45),    # 顶部水厂
    ("D1", "用户D1", "住宅", "C", 35, 40),          # 左侧
    ("B1", "用户B1", "学校", "B", 45, 40),          # 右侧（B级）
    ("C1", "用户C1", "住宅", "C", 40, 35)           # 底部
]

c.executemany("""
INSERT OR IGNORE INTO building_nodes
  (Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y)
VALUES (?,      ?,         ?,         ?,     ?,           ?)
""", network2_nodes)

# 添加管道
network2_pipes = [
    ("PD001", "WP002", "D1", 500, "正常"),  # 半径2.5，直径500
    ("PD002", "WP002", "B1", 600, "正常"),  # 半径3，直径600（B级用户）
    ("PD003", "D1", "C1", 300, "正常"),     # 半径1.5，直径300
    ("PD004", "B1", "C1", 400, "正常")      # 半径2，直径400
]

c.executemany("""
INSERT OR IGNORE INTO pipes
  (Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status)
VALUES (?,       ?,             ?,           ?,        ?)
""", network2_pipes)

# 添加阀门
network2_valves = [
    ("VD001", "PD001", "正常"),
    ("VD002", "PD002", "正常"),
    ("VD003", "PD003", "正常"),
    ("VD004", "PD004", "正常")
]

c.executemany("""
INSERT OR IGNORE INTO valves
  (Valve_ID, Controlled_Pipe_ID, Status)
VALUES (?,       ?,                 ?)
""", network2_valves)

print("✅ 网络2添加完成：WP002菱形网络")

# =============== 网络3：树形网络 ===============
print("\n📍 添加网络3：树形网络")

# 添加节点
network3_nodes = [
    ("WP003", "水厂WP003", "水厂", "A", 60, 70),    # 顶部水厂
    ("B2", "用户B2", "学校", "B", 55, 60),          # 左侧中层（B级）
    ("C2", "用户C2", "住宅", "C", 65, 60),          # 右侧中层（C级）
    ("D2", "用户D2", "住宅", "C", 60, 50)           # 底部（C级）
]

c.executemany("""
INSERT OR IGNORE INTO building_nodes
  (Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y)
VALUES (?,      ?,         ?,         ?,     ?,           ?)
""", network3_nodes)

# 添加管道（根据原图半径：WP003->B2(1), WP003->C2(2), B2->D2(4), C2->D2(3)）
network3_pipes = [
    ("PT001", "WP003", "B2", 200, "正常"),  # 半径1，直径200
    ("PT002", "WP003", "C2", 400, "正常"),  # 半径2，直径400
    ("PT003", "B2", "D2", 800, "正常"),     # 半径4，直径800
    ("PT004", "C2", "D2", 600, "正常")      # 半径3，直径600
]

c.executemany("""
INSERT OR IGNORE INTO pipes
  (Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status)
VALUES (?,       ?,             ?,           ?,        ?)
""", network3_pipes)

# 添加阀门
network3_valves = [
    ("VT001", "PT001", "正常"),
    ("VT002", "PT002", "正常"),
    ("VT003", "PT003", "正常"),
    ("VT004", "PT004", "正常")
]

c.executemany("""
INSERT OR IGNORE INTO valves
  (Valve_ID, Controlled_Pipe_ID, Status)
VALUES (?,       ?,                 ?)
""", network3_valves)

print("✅ 网络3添加完成：WP003树形网络")

# =============== 网络4：环形网络 ===============
print("\n📍 添加网络4：环形网络")

# 添加节点
network4_nodes = [
    ("test1", "用户Y1", "居民楼", "C", 2.5, 10),    # 水厂
    ("test2", "用户Y2", "居民楼", "C", 3, 10),          # B级用户
            # 额外节点形成更复杂网络
]

c.executemany("""
INSERT OR IGNORE INTO building_nodes
  (Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y)
VALUES (?,      ?,         ?,         ?,     ?,           ?)
""", network4_nodes)

# 添加管道（环形结构：D3 -> B3 -> WP004 -> C3 -> D3，加上额外连接）
network4_pipes = [
    ("P001", "WP001", "test1", 200, "正常"),  # B3->WP004
    ("P002", "PS003", "test1", 400, "正常"),  # WP004->C3
    ("P003", "WP001", "test2", 800, "正常"),     # D3->B3
    ("P004", "WP003", "test2", 600, "正常"),     # C3->D3
    ("P005", "test1", "test2", 300, "正常"),  # 额外连接
       # 额外连接
]

c.executemany("""
INSERT OR IGNORE INTO pipes
  (Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status)
VALUES (?,       ?,             ?,           ?,        ?)
""", network4_pipes)

# 添加阀门
network4_valves = [
    ("V001", "P001", "正常"),
    ("V002", "P002", "正常"),
    ("V003", "P003", "正常"),
    ("V004", "P004", "正常"),
    ("V005", "P005", "正常"),

]

c.executemany("""
INSERT OR IGNORE INTO valves
  (Valve_ID, Controlled_Pipe_ID, Status)
VALUES (?,       ?,                 ?)
""", network4_valves)

print("✅ 网络4添加完成：WP004环形网络")

# 提交所有更改
conn.commit()
conn.close()

print("\n🎉 所有网络结构已添加完成！")
print("\n📊 网络汇总：")
print("网络1 (简单型): WP001 -> S1/S2 -> ST")
print("网络2 (菱形型): WP002 菱形布局")
print("网络3 (树形型): WP003 -> B2/C2 -> D2")
print("网络4 (环形型): WP004 复杂环形网络")
print("\n💡 现在可以用不同的水厂节点测试各种隔离场景：")
print("- 测试WP001网络的S1节点漏损")
print("- 测试WP002网络的管道隔离")
print("- 测试WP003网络的D2节点隔离")
print("- 测试WP004网络的复杂隔离场景")