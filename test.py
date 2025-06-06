import matplotlib
matplotlib.use('TkAgg')  # 需在 plt 导入前设置后端
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 解决中文显示
matplotlib.rcParams['axes.unicode_minus'] = False   # 解决负号显示问题

import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd  # 导入 pandas

# 读取CSV文件（修改为你实际的文件路径）
edges_df = pd.read_csv(r"C:\Users\张鼎佐\Desktop\edges.csv")

# 创建有向图
G = nx.DiGraph()

# 添加节点和边到图中，确保容量被正确设置
for _, row in edges_df.iterrows():
    G.add_edge(row["source"], row["target"], capacity=row["capacity"])

# 打印所有节点，确认源节点和汇节点
print("图中的所有节点:", G.nodes())

# 获取用户输入的多个节点对
pairs_input = input("请输入多个节点对（例如 V1-U1,V2-U2）：")
pairs_list = pairs_input.split(",")  # 分割多个节点对

# 绘制拓扑结构
plt.figure(figsize=(8, 6))
pos = nx.spring_layout(G, seed=42)  # 使用spring布局，并设置种子确保布局一致

# 绘制图的节点和边
nx.draw(G, pos, with_labels=True, node_size=2000, node_color="lightblue", font_size=10, font_weight="bold")

# 显示权重（管道权重）
edge_labels = {(u, v): d["capacity"] for u, v, d in G.edges(data=True)}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

# 遍历每一对节点，计算最短路径并标记
for pair in pairs_list:
    source, target = pair.split("-")  # 分割成源节点和目标节点

    # 确保节点在图中
    if source in G.nodes() and target in G.nodes():
        # 计算最短路径
        shortest_path = nx.shortest_path(G, source=source, target=target, weight="capacity")
        print(f"{source} 到 {target} 的最短路径是:", shortest_path)

        # 标记最短路径的边为红色
        shortest_path_edges = [(shortest_path[i], shortest_path[i+1]) for i in range(len(shortest_path)-1)]
        nx.draw_networkx_edges(G, pos, edgelist=shortest_path_edges, edge_color="red", width=2)

        # 计算最小割（关闭阀门）
        flow_value, partition = nx.minimum_cut(G, source, target)
        reachable, non_reachable = partition
        cut_edges = []

        # 遍历最小割中的边，找出需要关闭的阀门
        for u, v in G.edges():
            if u in reachable and v in non_reachable:
                cut_edges.append((u, v))

        # 输出关闭的阀门
        print(f"需要关闭的阀门（切割的边）: {cut_edges}")

        # 在图上标记需要关闭的阀门
        nx.draw_networkx_edges(G, pos, edgelist=cut_edges, edge_color="green", width=2, style="dashed")
    else:
        print(f"输入的节点对 {source}-{target} 中有节点不在图中，请检查节点名称")

# 显示标题
plt.title(f"多对最短路径图与关闭阀门")
plt.show()
