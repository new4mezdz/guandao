import sqlite3

# 连接数据库
conn = sqlite3.connect("my_database.db")
c = conn.cursor()

print("🗑️ 正在删除WP003和WP004相关的网络数据...")

# =============== 删除WP003相关数据 ===============
print("\n📍 删除WP003树形网络...")

# 删除WP003相关的阀门
c.execute("DELETE FROM valves WHERE Valve_ID IN ('VT001', 'VT002', 'VT003', 'VT004')")
deleted_valves_wp003 = c.rowcount
print(f"✅ 删除了 {deleted_valves_wp003} 个WP003相关阀门")

# 删除WP003相关的管道
c.execute("DELETE FROM pipes WHERE Pipe_ID IN ('PT001', 'PT002', 'PT003', 'PT004')")
deleted_pipes_wp003 = c.rowcount
print(f"✅ 删除了 {deleted_pipes_wp003} 条WP003相关管道")

# 删除WP003相关的节点
c.execute("DELETE FROM building_nodes WHERE Node_ID IN ('WP003', 'B2', 'C2', 'D2')")
deleted_nodes_wp003 = c.rowcount
print(f"✅ 删除了 {deleted_nodes_wp003} 个WP003相关节点")

# =============== 删除WP004相关数据 ===============
print("\n📍 删除WP004环形网络...")

# 删除WP004相关的阀门
c.execute("DELETE FROM valves WHERE Valve_ID IN ('VE001', 'VE002', 'VE003', 'VE004', 'VE005', 'VE006')")
deleted_valves_wp004 = c.rowcount
print(f"✅ 删除了 {deleted_valves_wp004} 个WP004相关阀门")

# 删除WP004相关的管道
c.execute("DELETE FROM pipes WHERE Pipe_ID IN ('PE001', 'PE002', 'PE003', 'PE004', 'PE005', 'PE006')")
deleted_pipes_wp004 = c.rowcount
print(f"✅ 删除了 {deleted_pipes_wp004} 条WP004相关管道")

# 删除WP004相关的节点
c.execute("DELETE FROM building_nodes WHERE Node_ID IN ('WP004', 'B3', 'C3', 'D3', 'E3')")
deleted_nodes_wp004 = c.rowcount
print(f"✅ 删除了 {deleted_nodes_wp004} 个WP004相关节点")

# =============== 验证删除结果 ===============
print("\n🔍 验证删除结果...")

# 检查是否还有相关数据
c.execute("SELECT COUNT(*) FROM building_nodes WHERE Node_ID LIKE 'WP003%' OR Node_ID LIKE 'WP004%' OR Node_ID IN ('B2', 'C2', 'D2', 'B3', 'C3', 'D3', 'E3')")
remaining_nodes = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM pipes WHERE Pipe_ID LIKE 'PT%' OR Pipe_ID LIKE 'PE%'")
remaining_pipes = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM valves WHERE Valve_ID LIKE 'VT%' OR Valve_ID LIKE 'VE%'")
remaining_valves = c.fetchone()[0]

if remaining_nodes == 0 and remaining_pipes == 0 and remaining_valves == 0:
    print("✅ 所有WP003和WP004相关数据已完全删除")
else:
    print(f"⚠️ 仍有残留数据：节点{remaining_nodes}个，管道{remaining_pipes}条，阀门{remaining_valves}个")

# =============== 查看剩余网络 ===============
print("\n📊 剩余网络概览：")

c.execute("SELECT Node_ID, Node_Name, Level FROM building_nodes WHERE Level = 'A'")
water_plants = c.fetchall()
print("剩余水厂：")
for wp in water_plants:
    print(f"  {wp[0]}: {wp[1]} (等级{wp[2]})")

c.execute("SELECT COUNT(*) FROM building_nodes")
total_nodes = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM pipes")
total_pipes = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM valves")
total_valves = c.fetchone()[0]

print(f"\n当前数据库统计：")
print(f"  总节点数: {total_nodes}")
print(f"  总管道数: {total_pipes}")
print(f"  总阀门数: {total_valves}")

# 提交更改
conn.commit()
conn.close()

print("\n🎉 WP003和WP004网络删除完成！")
print("\n💡 现在数据库中应该只保留：")
print("- 原始的50节点网络")
print("- WP001简单s-t网络")
print("- WP002菱形网络")