import sqlite3

# 连接数据库
conn = sqlite3.connect("my_database.db")
c = conn.cursor()
# ✅ 插入“仅关闭 C 级无法隔离，需切断 B 级管道” 测试例子

# building_nodes
c.executescript("""
INSERT INTO building_nodes VALUES
('N500', 'A级源', '水厂', 'A', 50, 0),
('N501', 'B级用户', '学校', 'B', 51, 0),
('N502', 'C级用户1', '住宅', 'C', 52, -1),
('N503', 'C级用户2', '住宅', 'C', 52, 1),
('N504', '泄漏点', '住宅', 'C', 53, 1);
""")

# pipes
c.executescript("""
INSERT INTO pipes VALUES
('P500', 'N500', 'N501', 500, '正常'),
('P501', 'N501', 'N502', 300, '正常'),
('P502', 'N501', 'N503', 150, '正常'),
('P503', 'N503', 'N504', 150, '正常'),
('P504', 'N501', 'N504', 300, '正常');
""")

# valves
c.executescript("""
INSERT INTO valves VALUES
('V500', 'P500', '正常'),
('V501', 'P501', '正常'),
('V502', 'P502', '正常'),
('V503', 'P503', '正常'),
('V504', 'P504', '正常');
""")

print("✅ 已插入“仅关闭 C 级无法隔离，需切断 B 级管道” 测试例子")


# ✅ 提交事务并关闭连接
conn.commit()
conn.close()
print("🎉 全部插入完成！25 节点现实型供水网络已就绪")
