from flask import Flask, render_template, request, jsonify
import sqlite3
import json
import os
import traceback

app = Flask(__name__)

# 数据库路径
DB_PATH = '1.db'


def get_db_connection():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"数据库文件不存在: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/nodes')
def get_nodes():
    try:
        conn = get_db_connection()
        nodes = conn.execute(
            'SELECT Node_ID, Node_Name, Node_Type, Level, location_y as Latitude, location_x as Longitude FROM building_nodes').fetchall()
        conn.close()
        return jsonify([dict(node) for node in nodes])
    except Exception as e:
        print(f"Error in get_nodes: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# 更新节点位置接口
@app.route('/api/update_node_position', methods=['POST'])
def update_node_position():
    try:
        data = request.get_json()
        node_id = data.get('node_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if not node_id or latitude is None or longitude is None:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400

        conn = get_db_connection()

        # 更新数据库中的节点位置
        # 注意：location_y 对应 Latitude，location_x 对应 Longitude
        conn.execute('''
            UPDATE building_nodes 
            SET location_y = ?, location_x = ?
            WHERE Node_ID = ?
        ''', (latitude, longitude, node_id))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': '节点位置更新成功'})
    except Exception as e:
        print(f"Error in update_node_position: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500


# 添加新节点接口
@app.route('/api/add_node', methods=['POST'])
def add_node():
    try:
        data = request.get_json()
        node_id = data.get('node_id')
        node_name = data.get('node_name')
        node_type = data.get('node_type')
        level = data.get('level')
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if not node_id or not node_name or latitude is None or longitude is None:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400

        conn = get_db_connection()

        # 插入新节点
        # location_y 对应 Latitude，location_x 对应 Longitude
        conn.execute('''
            INSERT INTO building_nodes (Node_ID, Node_Name, Node_Type, Level, location_y, location_x)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (node_id, node_name, node_type, level, latitude, longitude))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': '节点添加成功'})
    except Exception as e:
        print(f"Error in add_node: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500


# 添加新管道接口
@app.route('/api/add_pipe', methods=['POST'])
def add_pipe():
    try:
        data = request.get_json()
        pipe_id = data.get('pipe_id')
        start_node_id = data.get('start_node_id')
        end_node_id = data.get('end_node_id')
        diameter = data.get('diameter', 0.5)
        status = data.get('status', 'Open')

        if not pipe_id or not start_node_id or not end_node_id:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400

        conn = get_db_connection()

        # 插入新管道
        conn.execute('''
            INSERT INTO pipes (Pipe_ID, Start_Node_ID, End_Node_ID, Diameter, Status)
            VALUES (?, ?, ?, ?, ?)
        ''', (pipe_id, start_node_id, end_node_id, diameter, status))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': '管道添加成功'})
    except Exception as e:
        print(f"Error in add_pipe: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500


# /api/pipes
@app.route('/api/pipes')
def get_pipes():
    try:
        conn = get_db_connection()
        pipes = conn.execute('''
            SELECT 
              Pipe_ID        AS pipe_id,
              Start_Node_ID  AS start_node_id,
              End_Node_ID    AS end_node_id,
              Diameter       AS diameter,
              Status         AS status
            FROM pipes
        ''').fetchall()
        conn.close()
        return jsonify([dict(pipe) for pipe in pipes])
    except Exception as e:
        print(f"Error in get_pipes: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# /api/valves
@app.route('/api/valves')
def get_valves():
    try:
        conn = get_db_connection()
        valves = conn.execute('''
            SELECT 
              Valve_ID           AS valve_id,
              Controlled_Pipe_ID AS pipe_id,
              Status             AS status
            FROM valves
        ''').fetchall()
        conn.close()
        return jsonify([dict(valve) for valve in valves])
    except Exception as e:
        print(f"Error in get_valves: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# /api/isolate/burst
@app.route('/api/isolate/burst', methods=['POST'])
def isolate_burst():
    try:
        data = request.get_json()
        pipe_id = data.get('pipe_id')

        conn = get_db_connection()

        pipe = conn.execute('''
            SELECT 
              Pipe_ID        AS pipe_id,
              Start_Node_ID  AS start_node_id,
              End_Node_ID    AS end_node_id
            FROM pipes WHERE Pipe_ID = ?
        ''', (pipe_id,)).fetchone()
        if not pipe:
            conn.close()
            return jsonify({'error': '管道不存在'}), 404

        valves = conn.execute('''
            SELECT 
              Valve_ID           AS valve_id,
              Controlled_Pipe_ID AS pipe_id,
              Status             AS status
            FROM valves WHERE Controlled_Pipe_ID = ?
        ''', (pipe_id,)).fetchall()

        affected_nodes = conn.execute('''
            SELECT * FROM building_nodes 
            WHERE Node_ID = ? OR Node_ID = ?
        ''', (pipe['start_node_id'], pipe['end_node_id'])).fetchall()

        conn.close()

        result = {
            'pipe_id': pipe_id,
            'valves_to_close': [dict(v) for v in valves],
            'affected_buildings': [dict(n) for n in affected_nodes],
            'affected_pipes': [pipe_id],
            'isolation_strategy': 'burst_pipe_emergency'
        }
        return jsonify(result)
    except Exception as e:
        print(f"Error in isolate_burst: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# /api/isolate/leak
@app.route('/api/isolate/leak', methods=['POST'])
def isolate_leak():
    try:
        data = request.get_json()
        pipe_id = data.get('pipe_id')

        conn = get_db_connection()

        pipe = conn.execute('''
            SELECT 
              Pipe_ID        AS pipe_id,
              Start_Node_ID  AS start_node_id,
              End_Node_ID    AS end_node_id
            FROM pipes WHERE Pipe_ID = ?
        ''', (pipe_id,)).fetchone()
        if not pipe:
            conn.close()
            return jsonify({'error': '管道不存在'}), 404

        valves = conn.execute('''
            SELECT 
              Valve_ID           AS valve_id,
              Controlled_Pipe_ID AS pipe_id,
              Status             AS status
            FROM valves WHERE Controlled_Pipe_ID = ?
        ''', (pipe_id,)).fetchall()

        affected_nodes = conn.execute('''
            SELECT * FROM building_nodes 
            WHERE Node_ID = ? OR Node_ID = ?
            ORDER BY Level ASC
        ''', (pipe['start_node_id'], pipe['end_node_id'])).fetchall()

        conn.close()

        result = {
            'pipe_id': pipe_id,
            'valves_to_close': [dict(v) for v in valves],
            'affected_buildings': [dict(n) for n in affected_nodes],
            'affected_pipes': [pipe_id],
            'isolation_strategy': 'pipe_leak_direct'
        }
        return jsonify(result)
    except Exception as e:
        print(f"Error in isolate_leak: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# /api/isolate/node
@app.route('/api/isolate/node', methods=['POST'])
def isolate_node():
    try:
        data = request.get_json()
        node_id = data.get('node_id')

        conn = get_db_connection()

        node = conn.execute('SELECT * FROM building_nodes WHERE Node_ID = ?', (node_id,)).fetchone()
        if not node:
            conn.close()
            return jsonify({'error': '节点不存在'}), 404

        connected_pipes = conn.execute('''
            SELECT 
              Pipe_ID        AS pipe_id,
              Start_Node_ID  AS start_node_id,
              End_Node_ID    AS end_node_id
            FROM pipes 
            WHERE Start_Node_ID = ? OR End_Node_ID = ?
        ''', (node_id, node_id)).fetchall()

        if len(connected_pipes) == 0:
            conn.close()
            return jsonify({
                'node_id': node_id,
                'node_info': dict(node),
                'valves_to_close': [],
                'affected_buildings': [],
                'isolation_strategy': 'no_pipes_connected'
            })

        pipe_ids = [p['pipe_id'] for p in connected_pipes]
        placeholders = ','.join('?' * len(pipe_ids))
        valves = conn.execute(f'''
            SELECT 
              Valve_ID           AS valve_id,
              Controlled_Pipe_ID AS pipe_id,
              Status             AS status
            FROM valves 
            WHERE Controlled_Pipe_ID IN ({placeholders})
        ''', pipe_ids).fetchall()

        affected_node_ids = set()
        for pipe in connected_pipes:
            affected_node_ids.add(pipe['start_node_id'])
            affected_node_ids.add(pipe['end_node_id'])
        affected_node_ids.discard(node_id)

        affected_nodes = []
        if affected_node_ids:
            placeholders = ','.join('?' * len(affected_node_ids))
            affected_nodes = conn.execute(
                f'SELECT * FROM building_nodes WHERE Node_ID IN ({placeholders}) ORDER BY Level ASC',
                list(affected_node_ids)
            ).fetchall()

        conn.close()

        result = {
            'node_id': node_id,
            'node_info': dict(node),
            'valves_to_close': [dict(v) for v in valves],
            'affected_buildings': [dict(n) for n in affected_nodes],
            'affected_pipes': pipe_ids,
            'isolation_strategy': 'node_leak_minimum_cut'
        }
        return jsonify(result)
    except Exception as e:
        print(f"Error in isolate_node: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)