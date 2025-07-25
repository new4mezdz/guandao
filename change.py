import sqlite3
conn = sqlite3.connect("my_database.db")
c = conn.cursor()
c.execute("UPDATE building_nodes SET Level='C' WHERE Node_ID='1'")
c.execute("UPDATE building_nodes SET Level='A' WHERE Node_ID='s'")
conn.commit()
conn.close()
print("已修改节点15为C，节点1为A")