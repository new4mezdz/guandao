import sqlite3

# 连接数据库
conn = sqlite3.connect("my_database.db")
c = conn.cursor()

c.executescript("""
INSERT INTO building_nodes VALUES
('N100', '测试源', '水厂', 'A', 10, 0),
('N101', '中转1', '中转', 'A', 11, 0),
('N102', '分支左', '用户', 'B', 12, -1),
('N103', '分支右', '用户', 'B', 12, 1),
('N104', '泄漏点', '用户', 'C', 13, 0);
""")

# pipes
c.executescript("""
INSERT INTO pipes VALUES
('P100', 'N100', 'N101', 500, '正常'),
('P101', 'N101', 'N102', 400, '正常'),
('P102', 'N101', 'N103', 100, '正常'),
('P103', 'N102', 'N104', 100, '正常'),
('P104', 'N103', 'N104', 100, '正常');
""")

# valves
c.executescript("""
INSERT INTO valves VALUES
('V100', 'P100', '正常'),
('V101', 'P101', '正常'),
('V102', 'P102', '正常'),
('V103', 'P103', '正常'),
('V104', 'P104', '正常');
""")

print("✅ 已插入最小割 vs 就近关阀 测试例子子图")

# ✅ 提交事务并关闭连接
conn.commit()
conn.close()
print("🎉 全部插入完成！25 节点现实型供水网络已就绪")
