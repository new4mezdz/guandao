import sqlite3
import random
import math
import numpy as np
from collections import defaultdict

# —— 配置参数 ——
random.seed(42)
np.random.seed(42)


class RealisticCityNetwork:
    def __init__(self, city_scale="medium", grid_size=None, total_nodes=None):
        """
        初始化城市供水网络
        city_scale: "small"(小城市), "medium"(中等城市), "large"(大城市), "custom"(自定义)
        """
        self.city_scale = city_scale

        # 根据城市规模设置参数
        if city_scale == "small":
            self.grid_size = 25
            self.total_nodes = 150
            self.min_distance = 0.8
        elif city_scale == "medium":
            self.grid_size = 40
            self.total_nodes = 400
            self.min_distance = 0.6
        elif city_scale == "large":
            self.grid_size = 60
            self.total_nodes = 800
            self.min_distance = 0.5
        elif city_scale == "custom":
            self.grid_size = grid_size or 30
            self.total_nodes = total_nodes or 200
            self.min_distance = 0.7
        else:
            # 默认中等规模
            self.grid_size = 30
            self.total_nodes = 200
            self.min_distance = 0.8

        self.nodes = []
        self.pipes = []
        self.valves = []
        self.pos = {}
        self.pipe_id_counter = 0  # 初始化管道ID计数器

        print(f"🏙️ 初始化 {city_scale} 规模城市: {self.total_nodes}节点, {self.grid_size}x{self.grid_size}网格")

    def generate_realistic_layout(self):
        """生成具有现实意义的城市布局"""

        # 根据城市规模调整设施数量
        scale_factor = self.total_nodes / 200  # 以200节点为基准

        # 1. 水源（水厂）- 数量随规模增加
        water_plants = []
        num_plants = max(2, int(2 + scale_factor * 0.5))  # 2-4个水厂

        # 水厂位置分布在城市边缘
        plant_positions = [
            (self.grid_size * 0.1, self.grid_size * 0.8),  # 左上
            (self.grid_size * 0.85, self.grid_size * 0.15),  # 右下
            (self.grid_size * 0.15, self.grid_size * 0.2),  # 左下
            (self.grid_size * 0.8, self.grid_size * 0.8)  # 右上
        ]

        for i in range(min(num_plants, len(plant_positions))):
            x, y = plant_positions[i]
            water_plants.append({
                'id': f'WP{i + 1:03d}',
                'name': f'第{i + 1}水厂',
                'type': '水厂',
                'level': 'A',
                'x': x, 'y': y,
                'capacity': 50000 - i * 10000  # 主厂容量更大
            })

        # 2. 泵站 - 数量按规模调整
        pump_stations = []
        num_pumps = max(4, int(4 + scale_factor * 2))  # 4-8个泵站

        # 泵站在城市中分散分布
        for i in range(num_pumps):
            angle = (2 * math.pi * i) / num_pumps  # 环形分布
            radius = self.grid_size * 0.3
            center_x, center_y = self.grid_size * 0.5, self.grid_size * 0.5
            x = center_x + radius * math.cos(angle) * random.uniform(0.8, 1.2)
            y = center_y + radius * math.sin(angle) * random.uniform(0.8, 1.2)

            # 确保在边界内
            x = max(self.grid_size * 0.1, min(self.grid_size * 0.9, x))
            y = max(self.grid_size * 0.1, min(self.grid_size * 0.9, y))

            pump_stations.append({
                'id': f'PS{i + 1:03d}',
                'name': f'第{i + 1}泵站',
                'type': '泵站',
                'level': 'A',
                'x': x, 'y': y,
                'capacity': 20000
            })

        # 3. 水塔 - 数量按规模调整
        water_towers = []
        num_towers = max(4, int(3 + scale_factor * 1.5))  # 3-6个水塔

        for i in range(num_towers):
            # 水塔分布在各个区域的制高点
            x = random.uniform(self.grid_size * 0.15, self.grid_size * 0.85)
            y = random.uniform(self.grid_size * 0.15, self.grid_size * 0.85)

            water_towers.append({
                'id': f'WT{i + 1:03d}',
                'name': f'第{i + 1}水塔',
                'type': '水塔',
                'level': 'A',
                'x': x, 'y': y,
                'capacity': 5000
            })

        # 4. DMA分区计量站 - 重要的中间节点
        dma_stations = []
        num_dmas = max(6, int(6 + scale_factor * 4))  # 6-20个DMA

        # DMA按网格分布，每个覆盖一定区域
        grid_dma = int(math.sqrt(num_dmas)) + 1
        for i in range(num_dmas):
            grid_x = i % grid_dma
            grid_y = i // grid_dma

            # 在网格单元内随机分布
            x = (grid_x + random.uniform(0.2, 0.8)) * (self.grid_size / grid_dma)
            y = (grid_y + random.uniform(0.2, 0.8)) * (self.grid_size / grid_dma)

            x = max(self.grid_size * 0.1, min(self.grid_size * 0.9, x))
            y = max(self.grid_size * 0.1, min(self.grid_size * 0.9, y))

            area_name = f"第{i + 1}片区"
            dma_stations.append({
                'id': f'DMA{i + 1:03d}',
                'name': f'{area_name}计量站',
                'type': '计量站',
                'level': 'B',
                'x': x, 'y': y
            })

        # 5. 重要用户 - B级，数量按比例
        important_users = []
        num_important = max(8, int(8 + scale_factor * 6))  # 8-20个重要用户

        # 医院 (20%)
        num_hospitals = max(2, num_important // 5)
        for i in range(num_hospitals):
            x = random.uniform(self.grid_size * 0.2, self.grid_size * 0.8)
            y = random.uniform(self.grid_size * 0.2, self.grid_size * 0.8)
            important_users.append({
                'id': f'HP{i + 1:03d}',
                'name': f'第{i + 1}医院',
                'type': '医院',
                'level': 'B',
                'x': x, 'y': y
            })

        # 学校 (30%)
        num_schools = max(2, int(num_important * 0.3))
        for i in range(num_schools):
            x = random.uniform(self.grid_size * 0.2, self.grid_size * 0.8)
            y = random.uniform(self.grid_size * 0.2, self.grid_size * 0.8)
            important_users.append({
                'id': f'SCH{i + 1:03d}',
                'name': f'第{i + 1}学校',
                'type': '学校',
                'level': 'B',
                'x': x, 'y': y
            })

        # 工厂 (20%)
        num_factories = max(1, num_important // 5)
        for i in range(num_factories):
            # 工厂多在城市边缘
            if random.random() < 0.5:
                x = random.uniform(self.grid_size * 0.05, self.grid_size * 0.25)
            else:
                x = random.uniform(self.grid_size * 0.75, self.grid_size * 0.95)
            y = random.uniform(self.grid_size * 0.1, self.grid_size * 0.9)

            important_users.append({
                'id': f'FAC{i + 1:03d}',
                'name': f'第{i + 1}工厂',
                'type': '工厂',
                'level': 'B',
                'x': x, 'y': y
            })

        # 其他重要用户 (商场、政府等)
        remaining_important = num_important - len(important_users)
        for i in range(remaining_important):
            x = random.uniform(self.grid_size * 0.2, self.grid_size * 0.8)
            y = random.uniform(self.grid_size * 0.2, self.grid_size * 0.8)
            important_users.append({
                'id': f'COM{i + 1:03d}',
                'name': f'商业区{i + 1}',
                'type': '商业',
                'level': 'B',
                'x': x, 'y': y
            })

        # 6. 居民小区 - C级用户，占大部分
        residential_areas = []
        remaining_nodes = self.total_nodes - len(water_plants) - len(pump_stations) - len(water_towers) - len(
            dma_stations) - len(important_users)

        # 已占用位置列表
        occupied_positions = []
        for node in water_plants + pump_stations + water_towers + dma_stations + important_users:
            occupied_positions.append((node['x'], node['y']))

        # 居民区按密度分布
        residential_zones = [
            {'center_ratio': (0.3, 0.7), 'radius_ratio': 0.15, 'density': 0.25, 'name': '老城区'},
            {'center_ratio': (0.6, 0.6), 'radius_ratio': 0.2, 'density': 0.3, 'name': '新城区'},
            {'center_ratio': (0.5, 0.4), 'radius_ratio': 0.18, 'density': 0.2, 'name': '中心区'},
            {'center_ratio': (0.8, 0.3), 'radius_ratio': 0.12, 'density': 0.15, 'name': '开发区'},
            {'center_ratio': (0.2, 0.3), 'radius_ratio': 0.1, 'density': 0.1, 'name': '工业区住宅'}
        ]

        node_count = 0
        for zone in residential_zones:
            zone_nodes = int(remaining_nodes * zone['density'])
            center_x = zone['center_ratio'][0] * self.grid_size
            center_y = zone['center_ratio'][1] * self.grid_size
            radius = zone['radius_ratio'] * self.grid_size

            attempts = 0
            for i in range(zone_nodes):
                if attempts > zone_nodes * 10:
                    break

                while attempts < zone_nodes * 10:
                    attempts += 1
                    angle = random.uniform(0, 2 * math.pi)
                    r = random.uniform(0.2, radius) * random.uniform(0.4, 1.0)
                    x = center_x + r * math.cos(angle)
                    y = center_y + r * math.sin(angle)

                    # 边界检查
                    x = max(self.grid_size * 0.05, min(self.grid_size * 0.95, x))
                    y = max(self.grid_size * 0.05, min(self.grid_size * 0.95, y))

                    # 最小距离检查
                    valid_position = True
                    for ox, oy in occupied_positions:
                        if math.hypot(x - ox, y - oy) < self.min_distance:
                            valid_position = False
                            break

                    if valid_position:
                        residential_areas.append({
                            'id': f'RES{node_count + 1:03d}',
                            'name': f'{zone["name"]}小区{i + 1}',
                            'type': '住宅',
                            'level': 'C',
                            'x': x, 'y': y
                        })
                        occupied_positions.append((x, y))
                        node_count += 1
                        break

                if node_count >= remaining_nodes:
                    break
            if node_count >= remaining_nodes:
                break

        # 合并所有节点
        all_nodes = water_plants + pump_stations + water_towers + dma_stations + important_users + residential_areas

        # 构建节点列表和位置字典
        for node in all_nodes:
            self.nodes.append((node['id'], node['name'], node['type'], node['level'], node['x'], node['y']))
            self.pos[node['id']] = (node['x'], node['y'])

        print(f"✅ 已生成 {len(self.nodes)} 个节点 (网格大小: {self.grid_size}x{self.grid_size}):")
        print(f"   - 水厂: {len(water_plants)}")
        print(f"   - 泵站: {len(pump_stations)}")
        print(f"   - 水塔: {len(water_towers)}")
        print(f"   - 计量站: {len(dma_stations)}")
        print(f"   - 重要用户: {len(important_users)}")
        print(f"   - 居民区: {len(residential_areas)}")
        print(f"   - 节点间最小距离: {self.min_distance}")

    def generate_realistic_pipes(self):
        """生成符合现实的管道连接"""

        # 分类节点
        water_plants = [n for n in self.nodes if n[2] == '水厂']
        pump_stations = [n for n in self.nodes if n[2] == '泵站']
        water_towers = [n for n in self.nodes if n[2] == '水塔']
        dma_stations = [n for n in self.nodes if n[2] == '计量站']
        important_users = [n for n in self.nodes if n[3] == 'B' and n[2] not in ['泵站', '水塔', '计量站']]
        residential = [n for n in self.nodes if n[3] == 'C']

        pipe_id_counter = 0

        def add_pipe(start_id, end_id, diameter, pipe_type="配水"):
            nonlocal pipe_id_counter
            pipe_id = f"P{pipe_id_counter:04d}"
            self.pipes.append((pipe_id, start_id, end_id, diameter, "正常"))
            self.valves.append((f"V{pipe_id_counter:04d}", pipe_id, "正常"))
            pipe_id_counter += 1
            return pipe_id

        # 1. 主干管网：水厂 -> 泵站 -> 水塔
        # 水厂到泵站（大口径主干管）
        for plant in water_plants:
            plant_id = plant[0]
            # 连接到最近的2个泵站
            distances = [(self.calculate_distance(plant_id, ps[0]), ps[0])
                         for ps in pump_stations]
            distances.sort()

            for dist, pump_id in distances[:2]:
                diameter = random.choice([800, 1000, 1200])  # 主干管大口径
                add_pipe(plant_id, pump_id, diameter, "主干管")
                print(f"主干管: {plant_id} -> {pump_id} (DN{diameter})")

        # 泵站到水塔
        for pump in pump_stations:
            pump_id = pump[0]
            # 每个泵站连接到最近的水塔
            if water_towers:
                distances = [(self.calculate_distance(pump_id, wt[0]), wt[0])
                             for wt in water_towers]
                distances.sort()

                for dist, tower_id in distances[:2]:  # 连接最近的2个水塔
                    diameter = random.choice([600, 800, 1000])
                    add_pipe(pump_id, tower_id, diameter, "输水管")

        # 2. 次级管网：水塔/泵站 -> DMA计量站
        supply_sources = pump_stations + water_towers  # 供水源
        for dma in dma_stations:
            dma_id = dma[0]
            # 连接到最近的供水源
            distances = [(self.calculate_distance(dma_id, src[0]), src[0])
                         for src in supply_sources]
            distances.sort()

            # 每个DMA至少连接1个，最多2个供水源（冗余）
            for dist, src_id in distances[:2]:
                diameter = random.choice([400, 500, 600])
                add_pipe(src_id, dma_id, diameter, "配水主管")

        # 3. 配水管网：DMA -> 重要用户 & 部分居民区
        for dma in dma_stations:
            dma_id = dma[0]
            dma_pos = self.pos[dma_id]

            # DMA覆盖范围内的用户（基于距离）
            coverage_radius = 4.5  # 扩大DMA覆盖半径
            covered_users = []

            # 重要用户优先覆盖
            for user in important_users:
                if self.calculate_distance(dma_id, user[0]) <= coverage_radius:
                    covered_users.append(user)

            # 部分居民区
            for res in residential:
                if self.calculate_distance(dma_id, res[0]) <= coverage_radius:
                    covered_users.append(res)

            # 连接到覆盖范围内的用户
            for user in covered_users[:8]:  # 每个DMA直接服务不超过8个用户
                diameter = random.choice([200, 250, 300])
                add_pipe(dma_id, user[0], diameter, "配水管")

        # 4. 建立居民区之间的环状连接（提高可靠性）
        self.create_neighborhood_connections(residential)

        # 5. 重要用户之间的备用连接
        self.create_backup_connections(important_users)

        print(f"✅ 已生成 {len(self.pipes)} 条管道")

    def create_neighborhood_connections(self, residential_nodes):
        """在居民区之间创建邻近连接，形成环状网络"""

        for i, res1 in enumerate(residential_nodes):
            # 找到最近的3-4个邻居
            distances = []
            for j, res2 in enumerate(residential_nodes):
                if i != j:
                    dist = self.calculate_distance(res1[0], res2[0])
                    if dist <= 3.0:  # 扩大连接距离
                        distances.append((dist, res2[0]))

            distances.sort()
            # 连接最近的2-3个邻居
            for dist, neighbor_id in distances[:random.randint(2, 3)]:
                # 避免重复连接
                existing = any((p[1] == neighbor_id and p[2] == res1[0]) or
                               (p[1] == res1[0] and p[2] == neighbor_id) for p in self.pipes)
                if not existing:
                    diameter = random.choice([100, 150, 200])  # 小口径配水管
                    pipe_id = f"P{self.pipe_id_counter:04d}"
                    self.pipes.append((pipe_id, res1[0], neighbor_id, diameter, "正常"))
                    self.valves.append((f"V{self.pipe_id_counter:04d}", pipe_id, "正常"))
                    self.pipe_id_counter += 1

    def create_backup_connections(self, important_users):
        """在重要用户之间创建备用连接"""
        pipe_id_counter = len(self.pipes)

        for i, user1 in enumerate(important_users):
            distances = []
            for j, user2 in enumerate(important_users):
                if i != j:
                    dist = self.calculate_distance(user1[0], user2[0])
                    if dist <= 6.0:  # 重要用户备用连接距离可以更远
                        distances.append((dist, user2[0]))

            distances.sort()
            # 每个重要用户连接1-2个其他重要用户作为备用
            for dist, backup_id in distances[:1]:
                existing = any((p[1] == backup_id and p[2] == user1[0]) or
                               (p[1] == user1[0] and p[2] == backup_id) for p in self.pipes)
                if not existing:
                    diameter = random.choice([250, 300, 400])
                    pipe_id = f"P{pipe_id_counter:04d}"
                    self.pipes.append((pipe_id, user1[0], backup_id, diameter, "正常"))
                    self.valves.append((f"V{pipe_id_counter:04d}", pipe_id, "正常"))
                    pipe_id_counter += 1

    def calculate_distance(self, node1_id, node2_id):
        """计算两节点间距离"""
        pos1 = self.pos[node1_id]
        pos2 = self.pos[node2_id]
        return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1])

    def ensure_connectivity(self):
        """确保网络连通性，补充必要连接"""
        # 构建邻接表检查连通性
        adj = defaultdict(list)
        for pipe in self.pipes:
            adj[pipe[1]].append(pipe[2])  # start -> end

        # 从水厂开始BFS
        water_plants = [n[0] for n in self.nodes if n[2] == '水厂']
        reachable = set(water_plants)
        queue = list(water_plants)

        while queue:
            cur = queue.pop(0)
            for neighbor in adj[cur]:
                if neighbor not in reachable:
                    reachable.add(neighbor)
                    queue.append(neighbor)

        # 找到不可达节点
        all_nodes = set(n[0] for n in self.nodes)
        unreachable = all_nodes - reachable

        if unreachable:
            print(f"⚠️ 发现 {len(unreachable)} 个不可达节点，正在补充连接...")
            pipe_id_counter = len(self.pipes)

            for node_id in unreachable:
                # 找最近的可达节点连接
                distances = [(self.calculate_distance(node_id, reach_id), reach_id)
                             for reach_id in reachable]
                distances.sort()

                nearest_id = distances[0][1]
                diameter = random.choice([150, 200, 250])
                pipe_id = f"P{pipe_id_counter:04d}"
                self.pipes.append((pipe_id, nearest_id, node_id, diameter, "正常"))
                self.valves.append((f"V{pipe_id_counter:04d}", pipe_id, "正常"))
                pipe_id_counter += 1

                # 更新可达集合
                reachable.add(node_id)
                adj[nearest_id].append(node_id)
                print(f"🔗 补充连接: {nearest_id} -> {node_id}")

    def save_to_database(self, db_path="my_database.db"):
        """保存到数据库"""

        # 先检查是否有重复的管道ID
        pipe_ids = [p[0] for p in self.pipes]
        unique_pipe_ids = set(pipe_ids)

        if len(pipe_ids) != len(unique_pipe_ids):
            print(f"❌ 发现重复的管道ID!")
            print(f"   总管道数: {len(pipe_ids)}")
            print(f"   唯一ID数: {len(unique_pipe_ids)}")

            # 找出重复的ID
            from collections import Counter
            id_counts = Counter(pipe_ids)
            duplicates = [pid for pid, count in id_counts.items() if count > 1]

            print(f"   重复的ID: {duplicates}")

            # 显示重复ID的详细信息
            for dup_id in duplicates[:5]:  # 只显示前5个
                duplicate_pipes = [p for p in self.pipes if p[0] == dup_id]
                print(f"   ID {dup_id} 重复 {len(duplicate_pipes)} 次:")
                for pipe in duplicate_pipes:
                    print(f"     {pipe}")

            # 重新分配ID
            print("🔧 正在重新分配管道ID...")
            new_pipes = []
            new_valves = []

            for i, (old_pipe_id, start, end, diameter, status) in enumerate(self.pipes):
                new_pipe_id = f"P{i:04d}"
                new_pipes.append((new_pipe_id, start, end, diameter, status))

                # 找到对应的阀门并更新
                old_valve = next((v for v in self.valves if v[1] == old_pipe_id), None)
                if old_valve:
                    new_valve_id = f"V{i:04d}"
                    new_valves.append((new_valve_id, new_pipe_id, old_valve[2]))

            self.pipes = new_pipes
            self.valves = new_valves
            print(f"✅ 已重新分配 {len(self.pipes)} 个管道ID")

        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # 清空旧数据
        c.execute("DELETE FROM valves")
        c.execute("DELETE FROM pipes")
        c.execute("DELETE FROM building_nodes")

        # 插入节点
        c.executemany("""
        INSERT INTO building_nodes
          (Node_ID, Node_Name, Node_Type, Level, Location_X, Location_Y)
        VALUES (?, ?, ?, ?, ?, ?)
        """, self.nodes)

        # 插入管道
        c.executemany("""
        INSERT INTO pipes
          (Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status)
        VALUES (?, ?, ?, ?, ?)
        """, self.pipes)

        # 插入阀门
        c.executemany("""
        INSERT INTO valves
          (Valve_ID, Controlled_Pipe_ID, Status)
        VALUES (?, ?, ?)
        """, self.valves)

        conn.commit()
        conn.close()

        print(f"✅ 已保存到数据库 {db_path}")
        print(f"   - 节点: {len(self.nodes)}")
        print(f"   - 管道: {len(self.pipes)}")
        print(f"   - 阀门: {len(self.valves)}")


def main():
    """主函数"""
    print("🏙️ 开始生成现实城市供水管网...")
    print("请选择城市规模:")
    print("1. 小城市 (150节点, 25x25网格) - 适合快速测试")
    print("2. 中等城市 (400节点, 40x40网格) - 平衡性能和真实性")
    print("3. 大城市 (800节点, 60x60网格) - 接近真实规模")
    print("4. 自定义")

    choice = input("请输入选择 (1-4): ").strip()

    if choice == "1":
        network = RealisticCityNetwork("small")
    elif choice == "2":
        network = RealisticCityNetwork("medium")
    elif choice == "3":
        network = RealisticCityNetwork("large")
    elif choice == "4":
        grid_size = int(input("请输入网格大小 (建议20-80): ") or 30)
        total_nodes = int(input("请输入总节点数 (建议100-1000): ") or 200)
        network = RealisticCityNetwork("custom", grid_size, total_nodes)
    else:
        print("使用默认中等规模...")
        network = RealisticCityNetwork("medium")

    # 生成布局
    network.generate_realistic_layout()

    # 生成管道
    network.generate_realistic_pipes()

    # 确保连通性
    network.ensure_connectivity()

    # 保存到数据库
    network.save_to_database()

    print("🎉 现实城市供水管网生成完成！")
    print("\n📊 网络特点:")
    print("  • 分层供水：水厂->泵站->水塔->DMA->用户")
    print("  • 分区管理：每个DMA覆盖一定区域")
    print("  • 等级保障：A级(水厂/泵站)>B级(重要用户)>C级(居民)")
    print("  • 备用连接：重要节点有冗余路径")
    print("  • 现实布局：按城市功能区域分布")
    print("  • 疏散布局：节点间保持合理距离，避免拥挤")
    print(f"  • 总规模：{network.total_nodes}节点, {len(network.pipes)}条管道")
    # 生成管道
    network.generate_realistic_pipes()

    # 确保连通性
    network.ensure_connectivity()

    # 保存到数据库
    network.save_to_database()

    print("🎉 现实城市供水管网生成完成！")
    print("\n📊 网络特点:")
    print("  • 分层供水：水厂->泵站->水塔->DMA->用户")
    print("  • 分区管理：每个DMA覆盖一定区域")
    print("  • 等级保障：A级(水厂/泵站)>B级(重要用户)>C级(居民)")
    print("  • 备用连接：重要节点有冗余路径")
    print("  • 现实布局：按城市功能区域分布")
    print("  • 疏散布局：节点间保持合理距离，避免拥挤")


if __name__ == "__main__":
    main()