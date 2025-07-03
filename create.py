import sqlite3

# 连接数据库
conn = sqlite3.connect("my_database.db")
c = conn.cursor()

# 执行建表 SQL
c.executescript("""
CREATE TABLE building_nodes (
    Node_ID TEXT PRIMARY KEY,
    Node_Name TEXT,
    Node_Type TEXT,
    Level TEXT, -- A / B / C
    Location_X REAL,
    Location_Y REAL
);

CREATE TABLE pipes (
    Pipe_ID TEXT PRIMARY KEY,
    Start_Node_ID TEXT,
    End_Node_ID TEXT,
    Diameter REAL, -- mm
    Status TEXT, -- 正常 / 维修 / 停用
    FOREIGN KEY (Start_Node_ID) REFERENCES building_nodes(Node_ID),
    FOREIGN KEY (End_Node_ID) REFERENCES building_nodes(Node_ID)
);

CREATE TABLE valves (
    Valve_ID TEXT PRIMARY KEY,
    Controlled_Pipe_ID TEXT,
    Status TEXT, -- 正常 / 失灵
    FOREIGN KEY (Controlled_Pipe_ID) REFERENCES pipes(Pipe_ID)
);
""")

# 提交事务
conn.commit()
conn.close()
