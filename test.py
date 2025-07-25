# debug_test.py - 调试版本，会输出详细信息
import sqlite3
import matplotlib

matplotlib.use('Agg')  # 保存文件模式
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from isolate_leakage import isolate_leakage
import time
import os


def debug_database():
    """调试数据库内容"""
    print("🔍 正在检查数据库内容...")

    conn = sqlite3.connect("my_database.db")
    c = conn.cursor()

    # 检查节点数据
    c.execute("SELECT COUNT(*) FROM building_nodes")
    node_count = c.fetchone()[0]
    print(f"📊 节点总数: {node_count}")

    if node_count > 0:
        c.execute("SELECT Node_ID, Node_Name, Level, Location_X, Location_Y FROM building_nodes LIMIT 5")
        sample_nodes = c.fetchall()
        print("📋 节点样本:")
        for node in sample_nodes:
            print(f"   {node}")

    # 检查管道数据
    c.execute("SELECT COUNT(*) FROM pipes")
    pipe_count = c.fetchone()[0]
    print(f"📊 管道总数: {pipe_count}")

    if pipe_count > 0:
        c.execute("SELECT Pipe_ID, Start_Node_ID, End_Node_ID FROM pipes LIMIT 5")
        sample_pipes = c.fetchall()
        print("📋 管道样本:")
        for pipe in sample_pipes:
            print(f"   {pipe}")

    # 检查坐标范围
    c.execute("SELECT MIN(Location_X), MAX(Location_X), MIN(Location_Y), MAX(Location_Y) FROM building_nodes")
    coord_range = c.fetchone()
    print(f"📍 坐标范围: X({coord_range[0]:.2f} ~ {coord_range[1]:.2f}), Y({coord_range[2]:.2f} ~ {coord_range[3]:.2f})")

    conn.close()
    return node_count > 0 and pipe_count > 0


def create_test_visualization():
    """创建测试可视化"""
    print("\n🎨 开始创建可视化...")

    # 读取数据
    conn = sqlite3.connect("my_database.db")
    c = conn.cursor()

    c.execute("SELECT Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y FROM building_nodes")
    nodes = c.fetchall()

    c.execute("SELECT Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status FROM pipes")
    pipes = c.fetchall()

    conn.close()

    print(f"✅ 读取到 {len(nodes)} 个节点, {len(pipes)} 条管道")

    if not nodes or not pipes:
        print("❌ 数据为空，无法绘图！")
        return False

    # 创建图形
    plt.figure(figsize=(12, 8))
    plt.clf()  # 清除之前的内容

    # 节点位置
    pos = {}
    x_coords = []
    y_coords = []
    node_colors = []
    node_labels = []

    color_map = {'A': 'red', 'B': 'orange', 'C': 'lightgreen'}

    for node in nodes:
        node_id, name, node_type, level, x, y = node
        pos[node_id] = (x, y)
        x_coords.append(x)
        y_coords.append(y)
        node_colors.append(color_map.get(level, 'gray'))
        node_labels.append(node_id)

    print(f"📍 节点坐标范围: X({min(x_coords):.2f}~{max(x_coords):.2f}), Y({min(y_coords):.2f}~{max(y_coords):.2f})")

    # 绘制节点
    scatter = plt.scatter(x_coords, y_coords, c=node_colors, s=300, alpha=0.8,
                          zorder=3, edgecolors='black', linewidth=2)

    # 添加节点标签
    for i, label in enumerate(node_labels):
        plt.annotate(label, (x_coords[i], y_coords[i]),
                     xytext=(8, 8), textcoords='offset points',
                     fontsize=10, ha='left', fontweight='bold',
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    # 绘制管道
    pipe_count = 0
    for pipe in pipes:
        pipe_id, start, end, diameter, status = pipe

        if start in pos and end in pos:
            x0, y0 = pos[start]
            x1, y1 = pos[end]

            # 绘制简单的线（先不用箭头）
            plt.plot([x0, x1], [y0, y1], 'b-', linewidth=2, alpha=0.6)
            pipe_count += 1
        else:
            print(f"⚠️ 管道 {pipe_id} 的节点不存在: {start} -> {end}")

    print(f"✅ 成功绘制 {pipe_count} 条管道")

    # 设置图形属性
    plt.title('供水网络图 - 测试版本', fontsize=14, fontweight='bold')
    plt.xlabel('X坐标')
    plt.ylabel('Y坐标')
    plt.grid(True, alpha=0.3)

    # 添加图例
    import matplotlib.patches as mpatches
    red_patch = mpatches.Patch(color='red', label='A级(水厂)')
    orange_patch = mpatches.Patch(color='orange', label='B级(学校)')
    green_patch = mpatches.Patch(color='lightgreen', label='C级(住宅)')
    plt.legend(handles=[red_patch, orange_patch, green_patch], loc='upper right')

    # 设置坐标轴范围
    plt.xlim(min(x_coords) - 1, max(x_coords) + 1)
    plt.ylim(min(y_coords) - 1, max(y_coords) + 1)

    plt.tight_layout()

    # 保存图片
    output_file = f"test_network_{int(time.time())}.png"
    plt.savefig(output_file, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()  # 关闭图形以释放内存

    print(f"📁 测试图片已保存: {output_file}")

    # 检查文件是否创建成功
    if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
        print("✅ 图片文件创建成功！")
        return True
    else:
        print("❌ 图片文件创建失败或文件过小！")
        return False


def main_with_debug():
    """主函数 - 调试版本"""
    print("🚀 调试版本 - 漏损隔离测试")

    # 首先检查数据库
    if not debug_database():
        print("❌ 数据库检查失败，请先运行 create.py 生成数据")
        return

    # 创建测试可视化
    if not create_test_visualization():
        print("❌ 测试可视化失败")
        return

    print("\n" + "=" * 50)
    print("继续进行隔离测试...")
    print("=" * 50)

    # 用户输入
    print("请选择漏损类型：\n1. 节点漏损\n2. 管道漏损\n3. 爆管")
    leak_mode = input("输入数字选择类型：").strip()

    if leak_mode == '1':
        leak_type = '普通漏损'
        leak_node = input("请输入漏损节点ID：").strip().upper()
        leak_node_pairs = []
        conn = sqlite3.connect("my_database.db")
        c = conn.cursor()
        c.execute("SELECT Start_Node_ID FROM pipes WHERE End_Node_ID=?", (leak_node,))
        starts = c.fetchall()
        leak_node_pairs = [(s[0], leak_node) for s in starts]
        conn.close()
        print(f"自动识别节点漏损相关管道: {leak_node_pairs}")
        fail_valve_id = input("请输入失效阀门ID（或无）：").strip().upper()

    elif leak_mode == '2':
        leak_type = '普通漏损'
        pipe_id = input("请输入漏损管道ID：").strip().upper()
        conn = sqlite3.connect("my_database.db")
        c = conn.cursor()
        c.execute("SELECT Start_Node_ID, End_Node_ID FROM pipes WHERE Pipe_ID=?", (pipe_id,))
        row = c.fetchone()
        if not row:
            print("❌ 未找到该管道！")
            return
        start, end = row
        leak_node_pairs = [(start, end)]
        fail_valve_id = input("请输入失效阀门ID（或无）：").strip().upper()
        conn.close()

    elif leak_mode == '3':
        leak_type = '爆管'
        pipe_id = input("请输入爆管管道ID：").strip().upper()
        conn = sqlite3.connect("my_database.db")
        c = conn.cursor()
        c.execute("SELECT Start_Node_ID, End_Node_ID FROM pipes WHERE Pipe_ID=?", (pipe_id,))
        row = c.fetchone()
        if not row:
            print("❌ 未找到该管道！")
            return
        start, end = row
        leak_node_pairs = [(start, end)]
        fail_valve_id = input("请输入失效阀门ID（或无）：").strip().upper()
        conn.close()
    else:
        print("❌ 无效选择，退出。")
        return

    # 调用隔离算法
    print(f"\n🔍 开始隔离分析: {leak_node_pairs}, 类型: {leak_type}")
    result = isolate_leakage(leak_node_pairs, leak_type, fail_valve_id)

    # 输出结果
    print("\n🔷 隔离结果")
    print("➡️ 需要关闭的阀门:", result.get("need_close_valves"))
    print("➡️ 失效阀门:", result.get("lost_valves"))
    print("➡️ 是否可隔离:", result.get("isolatable"))
    print("➡️ cut 边:", result.get("cut_edges"))
    print("➡️ 建议:", result.get("recommendation"))


if __name__ == "__main__":
    main_with_debug()