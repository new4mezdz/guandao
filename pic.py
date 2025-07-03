import sqlite3
import networkx as nx
import plotly.graph_objs as go
import plotly.io as pio

# 设置 plotly 默认渲染器为浏览器
pio.renderers.default = "browser"

# 连接数据库
conn = sqlite3.connect("my_database.db")
c = conn.cursor()

# 读取 building_nodes
c.execute("SELECT Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y FROM building_nodes")
nodes = c.fetchall()

# 读取 pipes
c.execute("SELECT Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status FROM pipes")
pipes = c.fetchall()

conn.close()

# 创建 NetworkX 有向图
G = nx.DiGraph()

# 添加节点
for node in nodes:
    node_id, name, node_type, level, x, y = node
    G.add_node(node_id, name=name, type=node_type, level=level, pos=(x, y))

# 添加边
for pipe in pipes:
    pipe_id, start, end, diameter, status = pipe
    capacity = diameter ** 2
    G.add_edge(start, end,
               pipe_id=pipe_id,
               diameter=diameter,
               status=status,
               capacity=capacity)

print(f"✅ 已生成 NetworkX 图：{G.number_of_nodes()} 节点，{G.number_of_edges()} 边")

# 使用坐标作为布局
pos = {node[0]: (node[4], node[5]) for node in nodes}

# 创建 plotly 边 trace
edge_trace = go.Scatter(
    x=[], y=[],
    line=dict(width=1, color='#888'),
    hoverinfo='none',
    mode='lines')

for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_trace['x'] += (x0, x1, None)
    edge_trace['y'] += (y0, y1, None)

# 创建 plotly 节点 trace（仅点）
node_trace = go.Scatter(
    x=[], y=[], text=[],
    mode='markers',
    hoverinfo='text',
    marker=dict(
        showscale=False,
        color=[],
        size=20,
        line=dict(width=2))
)

# 添加节点位置、颜色和 hover 信息
for node in G.nodes(data=True):
    x, y = pos[node[0]]
    node_trace['x'] += (x,)
    node_trace['y'] += (y,)
    level = node[1]['level']
    color = {'A': 'red', 'B': 'orange', 'C': 'green'}.get(level, 'gray')
    node_trace['marker']['color'] += (color,)
    name = node[1]['name']
    node_trace['text'] += (f"{node[0]} ({name}, {level})",)

# 创建节点标签 trace（显示在右侧）
label_trace = go.Scatter(
    x=[pos[n][0] + 0.05 for n in G.nodes()],  # x 坐标右移 0.05
    y=[pos[n][1] for n in G.nodes()],
    mode='text',
    text=[n for n in G.nodes()],
    textposition="middle right",
    hoverinfo='none',
    showlegend=False,
    textfont=dict(
        size=10,
        color='black'
    )
)

# 生成 plotly figure
fig = go.Figure(data=[edge_trace, node_trace, label_trace],
                layout=go.Layout(
                    title='🏞️ 25节点现实布局供水网络 - Plotly 交互展示（Node_ID 显示在右侧）',
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
               )

# 添加真正箭头 annotation
for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    fig.add_annotation(
        x=x1,
        y=y1,
        ax=x0,
        ay=y0,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=3,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="blue"
    )

fig.show()
