import sqlite3
import networkx as nx
import plotly.graph_objs as go
import plotly.io as pio
from isolate_leakage import isolate_leakage

# 设置 plotly 默认渲染器为浏览器
pio.renderers.default = "browser"

# 用户输入
leak_pipe_id = input("请输入泄漏管道ID：").strip()
leak_type = input("请输入泄漏类型（普通漏损/爆管）：").strip()
fail_valve_id = input("请输入失效阀门ID（或无）：").strip()

# 调用算法
result = isolate_leakage(leak_pipe_id, leak_type, fail_valve_id)

# 输出结果
print("\n🔷 测试结果")
print("➡️ 需要关闭的阀门:", result.get("need_close_valves"))
print("➡️ 失效阀门:", result.get("lost_valves"))
print("➡️ 是否可隔离:", result.get("isolatable"))
print("➡️ cut 边:", result.get("cut_edges"))
print("➡️ 建议:", result.get("recommendation"))

# 连接数据库
conn = sqlite3.connect("my_database.db")
c = conn.cursor()

# 读取 building_nodes
c.execute("SELECT Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y FROM building_nodes")
nodes = c.fetchall()

# 读取 pipes
c.execute("SELECT Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status FROM pipes")
pipes = c.fetchall()

# 读取 valves
c.execute("SELECT Valve_ID, Controlled_Pipe_ID, Status FROM valves")
valves = c.fetchall()

conn.close()

# 创建 NetworkX 有向图
G = nx.DiGraph()
for node in nodes:
    node_id, name, node_type, level, x, y = node
    G.add_node(node_id, name=name, type=node_type, level=level, pos=(x, y))

# 添加边
for pipe in pipes:
    pipe_id, start, end, diameter, status = pipe
    G.add_edge(start, end,
               pipe_id=pipe_id,
               diameter=diameter,
               status=status,
               capacity=diameter**2)

# 使用坐标作为布局
pos = {node[0]: (node[4], node[5]) for node in nodes}

# ✅ 生成需要关闭的管道列表
need_close_pipes = []

if leak_type == "爆管":
    need_close_pipes = [v[1] for v in valves if v[0] in result.get("need_close_valves", [])]
elif leak_type == "普通漏损":
    cut_edges = result.get("cut_edges", [])
    for u, v in cut_edges:
        if G.has_edge(u, v):
            need_close_pipes.append(G[u][v]['pipe_id'])

# 去重 + strip + upper
need_close_pipes = list(set([p.strip().upper() for p in need_close_pipes]))

# ✅ debug
print("🔴 最终 need_close_pipes:", need_close_pipes)

# 生成 edge traces，每条边单独 trace 以支持不同颜色
edge_traces = []
for edge in G.edges(data=True):
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    pipe_id = edge[2]['pipe_id'].strip().upper()
    color = 'red' if pipe_id in need_close_pipes else '#888'
    width = 6 if color == 'red' else 2

    trace = go.Scatter(
        x=[x0, x1],
        y=[y0, y1],
        line=dict(width=width, color=color),
        hoverinfo='text',
        text=[pipe_id],
        mode='lines'
    )
    edge_traces.append(trace)

# 创建节点 trace
node_trace = go.Scatter(
    x=[], y=[], text=[],
    mode='markers+text',
    hoverinfo='text',
    textposition="middle right",
    marker=dict(
        showscale=False,
        color=[],
        size=20,
        line=dict(width=2))
)

for node in G.nodes(data=True):
    x, y = pos[node[0]]
    node_trace['x'] += (x,)
    node_trace['y'] += (y,)
    level = node[1]['level']
    color = {'A': 'red', 'B': 'orange', 'C': 'green'}.get(level, 'gray')
    node_trace['marker']['color'] += (color,)
    name = node[1]['name']
    node_trace['text'] += (node[0],)

# 生成 plotly figure
fig = go.Figure(data=edge_traces + [node_trace],
                layout=go.Layout(
                    title='🏞️ 测试结果网络图（需关闭管道标红加粗）',
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20, l=5, r=5, t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    shapes=[
                        dict(
                            type="line",
                            x0=pos[edge[0]][0], y0=pos[edge[0]][1],
                            x1=pos[edge[1]][0], y1=pos[edge[1]][1],
                            line=dict(color="blue", width=1),
                            layer="above"
                        )
                        for edge in G.edges()
                    ]
                )
               )

fig.show()
