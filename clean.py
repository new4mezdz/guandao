import sqlite3
import os


def clean_database(db_path="my_database.db", recreate_tables=True):
    """
    清理数据库，可选择是否重新创建表结构

    参数:
        db_path: 数据库文件路径
        recreate_tables: 是否重新创建表结构
    """

    print(f"🔄 开始清理数据库: {db_path}")

    # 方法1：删除数据库文件（最彻底）
    if os.path.exists(db_path):
        choice = input("选择清理方式:\n1. 仅清空数据表\n2. 完全删除数据库文件\n请输入选择 (1/2): ").strip()

        if choice == "2":
            os.remove(db_path)
            print(f"✅ 已删除数据库文件: {db_path}")

            if recreate_tables:
                print("🔨 正在重新创建数据库和表结构...")
                create_database_tables(db_path)
            return

    # 方法2：仅清空数据表
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # 检查表是否存在
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = c.fetchall()
        print(f"📊 发现表: {[table[0] for table in tables]}")

        # 清空数据表
        tables_to_clean = ['valves', 'pipes', 'building_nodes']
        for table_name in tables_to_clean:
            try:
                c.execute(f"DELETE FROM {table_name}")
                c.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")  # 重置自增ID
                print(f"✅ 已清空表: {table_name}")
            except sqlite3.OperationalError as e:
                if "no such table" in str(e):
                    print(f"⚠️ 表不存在: {table_name}")
                else:
                    print(f"❌ 清空表失败 {table_name}: {e}")

        conn.commit()
        conn.close()
        print("✅ 数据表清理完成")

    except Exception as e:
        print(f"❌ 数据库清理失败: {e}")


def create_database_tables(db_path="my_database.db"):
    """创建数据库表结构"""

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # 创建 building_nodes 表
    c.execute('''
    CREATE TABLE IF NOT EXISTS building_nodes (
        Node_ID TEXT PRIMARY KEY,
        Node_Name TEXT NOT NULL,
        Node_Type TEXT NOT NULL,
        Level TEXT NOT NULL,
        Location_X REAL NOT NULL,
        Location_Y REAL NOT NULL,
        Created_Time DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 创建 pipes 表
    c.execute('''
    CREATE TABLE IF NOT EXISTS pipes (
        Pipe_ID TEXT PRIMARY KEY,
        Start_Node_ID TEXT NOT NULL,
        End_Node_ID TEXT NOT NULL,
        Diameter INTEGER NOT NULL,
        Status TEXT DEFAULT '正常',
        Length REAL,
        Material TEXT DEFAULT 'HDPE',
        Install_Date DATE,
        Created_Time DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (Start_Node_ID) REFERENCES building_nodes (Node_ID),
        FOREIGN KEY (End_Node_ID) REFERENCES building_nodes (Node_ID)
    )
    ''')

    # 创建 valves 表
    c.execute('''
    CREATE TABLE IF NOT EXISTS valves (
        Valve_ID TEXT PRIMARY KEY,
        Controlled_Pipe_ID TEXT NOT NULL,
        Status TEXT DEFAULT '正常',
        Valve_Type TEXT DEFAULT '闸阀',
        Install_Date DATE,
        Created_Time DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (Controlled_Pipe_ID) REFERENCES pipes (Pipe_ID)
    )
    ''')

    # 创建索引以提高查询性能
    c.execute('CREATE INDEX IF NOT EXISTS idx_pipes_start ON pipes (Start_Node_ID);')
    c.execute('CREATE INDEX IF NOT EXISTS idx_pipes_end ON pipes (End_Node_ID);')
    c.execute('CREATE INDEX IF NOT EXISTS idx_valves_pipe ON valves (Controlled_Pipe_ID);')
    c.execute('CREATE INDEX IF NOT EXISTS idx_nodes_level ON building_nodes (Level);')

    conn.commit()
    conn.close()

    print("✅ 数据库表结构创建完成")
    print("📋 创建的表:")
    print("   - building_nodes: 节点信息表")
    print("   - pipes: 管道信息表")
    print("   - valves: 阀门信息表")


def check_database_status(db_path="my_database.db"):
    """检查数据库状态"""

    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        print(f"📊 数据库状态检查: {db_path}")
        print("=" * 50)

        # 检查表和数据量
        tables = ['building_nodes', 'pipes', 'valves']
        for table in tables:
            try:
                c.execute(f"SELECT COUNT(*) FROM {table}")
                count = c.fetchone()[0]
                print(f"   {table:15}: {count:6} 条记录")
            except sqlite3.OperationalError:
                print(f"   {table:15}: 表不存在")

        print("=" * 50)

        # 检查是否有重复ID
        for table, id_column in [('building_nodes', 'Node_ID'), ('pipes', 'Pipe_ID'), ('valves', 'Valve_ID')]:
            try:
                c.execute(f"SELECT {id_column}, COUNT(*) FROM {table} GROUP BY {id_column} HAVING COUNT(*) > 1")
                duplicates = c.fetchall()
                if duplicates:
                    print(f"⚠️ {table} 表发现重复ID: {len(duplicates)} 个")
                    for dup_id, count in duplicates[:5]:  # 只显示前5个
                        print(f"     ID: {dup_id} (重复 {count} 次)")
                else:
                    print(f"✅ {table} 表无重复ID")
            except sqlite3.OperationalError:
                continue

        conn.close()

    except Exception as e:
        print(f"❌ 检查数据库失败: {e}")


def main():
    """主函数"""
    print("🗃️ 数据库清理工具")
    print("=" * 40)

    # 检查当前状态
    check_database_status()

    print("\n请选择操作:")
    print("1. 清理数据库")
    print("2. 仅查看状态")
    print("3. 创建/重建表结构")
    print("4. 退出")

    choice = input("请输入选择 (1-4): ").strip()

    if choice == "1":
        clean_database()
        print("\n清理后状态:")
        check_database_status()
    elif choice == "2":
        pass  # 已经显示了状态
    elif choice == "3":
        create_database_tables()
        check_database_status()
    elif choice == "4":
        print("👋 退出")
        return
    else:
        print("❌ 无效选择")


if __name__ == "__main__":
    main()