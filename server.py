import logging
import os
import shutil
import signal
import socket
import sqlite3
import sys
import time
import warnings
from datetime import datetime
from gevent.pywsgi import WSGIServer
from flask import Flask, request, jsonify, send_file, render_template
import json

app = Flask(__name__)


# Initialize SQLite database
def init_db():
    Devicesconn = sqlite3.connect('devices.db')
    Devicescursor = Devicesconn.cursor()
    Devicescursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT NOT NULL,
            ip_address TEXT NOT NULL
        )
    ''')
    Devicescursor.execute('''
        CREATE TABLE IF NOT EXISTS device_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            data TEXT,
            FOREIGN KEY(device_id) REFERENCES devices(id)
        )
    ''')
    Devicesconn.commit()
    Devicesconn.close()
    print("Device database initialized")

    Matchconn = sqlite3.connect('match.db')
    Matchcursor = Matchconn.cursor()
    Matchcursor.execute('''
        CREATE TABLE IF NOT EXISTS event (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id TEXT NOT NULL,
            match_data TEXT NOT NULL
        )
    ''')
    Matchconn.commit()
    Matchconn.close()
    print("Match database initialized")


@app.route('/')
def index():
    return render_template('index.html')


# HTML and JSON endpoints for devices
@app.route('/devices', methods=['GET'])
def get_devices():
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, device_name, ip_address FROM devices')
    devices = cursor.fetchall()
    conn.close()
    print(f"Devices fetched: {devices}")
    return render_template('devices.html', devices=devices)


@app.route('/api/devices', methods=['GET'])
def get_devices_json():
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, device_name, ip_address FROM devices')
    devices = cursor.fetchall()
    conn.close()
    print(f"Devices fetched: {devices}")
    return jsonify(devices)


# HTML and JSON endpoints for data
@app.route('/get_data', methods=['GET'])
def get_data_all():
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.device_name, dd.data
        FROM device_data dd
        JOIN devices d ON dd.device_id = d.id
    ''')
    data = cursor.fetchall()
    conn.close()
    print(f"Data fetched: {data}")
    return render_template('data.html', data=data)


@app.route('/api/get_data', methods=['GET'])
def get_data_all_json():
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.device_name, dd.data
        FROM device_data dd
        JOIN devices d ON dd.device_id = d.id
    ''')
    data = cursor.fetchall()
    conn.close()
    print(f"Data fetched: {data}")
    return jsonify(data)


# HTML and JSON endpoints for device-specific data
@app.route('/get_data/<device_id>', methods=['GET'])
def get_data(device_id):
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.device_name, dd.data
        FROM device_data dd
        JOIN devices d ON dd.device_id = d.id
        WHERE d.id = ?
    ''', (device_id,))
    data = cursor.fetchall()
    conn.close()
    print(f"Data fetched for device {device_id}: {data}")
    return render_template('data.html', data=data)


@app.route('/api/get_data/<device_id>', methods=['GET'])
def get_data_json(device_id):
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.device_name, dd.data
        FROM device_data dd
        JOIN devices d ON dd.device_id = d.id
        WHERE d.id = ?
    ''', (device_id,))
    data = cursor.fetchall()
    conn.close()
    print(f"Data fetched for device {device_id}: {data}")
    return jsonify(data)


@app.route('/send_data', methods=['POST'])
def send_data():
    data = request.json
    device_ip = request.remote_addr
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM devices WHERE ip_address = ?', (device_ip,))
    device = cursor.fetchone()
    if device:
        device_id = device[0]
        cursor.execute('INSERT INTO device_data (device_id, data) VALUES (?, ?)', (device_id, str(data)))
        conn.commit()
        print(f"Data inserted for device {device_id}: {data}")
    else:
        print(f"No device found with IP: {device_ip}")
    conn.close()
    return jsonify({"status": "success"})


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    device_name = data['device_name']
    device_ip = request.remote_addr
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM devices WHERE ip_address = ?', (device_ip,))
    device = cursor.fetchone()
    if device:
        cursor.execute('UPDATE devices SET device_name = ? WHERE ip_address = ?', (device_name, device_ip))
        conn.commit()
        conn.close()
        message = f"Device with IP: {device_ip} already registered. Refreshed with new name: {device_name}"
        print(message)
        return jsonify({"status": "success", "message": message})
    else:
        cursor.execute('INSERT INTO devices (device_name, ip_address) VALUES (?, ?)', (device_name, device_ip))
        conn.commit()
        conn.close()
        print(f"Registered device: {device_name} with IP: {device_ip}")
        return jsonify({"status": "success"})


@app.route('/client_images/getAndroid', methods=['POST'])
def getAndroid():
    file_path = os.path.join(os.getcwd(), 'App', 'app-release.apk')
    return send_file(file_path, as_attachment=True)


@app.route('/client_images/getServer', methods=['GET'])
def getServer():
    file_path = os.path.join(os.getcwd(), 'App', 'server.exe')
    return send_file(file_path, as_attachment=True)


@app.route('/client_images/getWindows', methods=['GET'])
def getWindows():
    return send_file('./App/app-release.apk', as_attachment=True)


@app.route('/client_images', methods=['GET'])
def client_images():
    return render_template('client_images.html')


@app.route('/clear_data', methods=['GET'])
def clear_data():
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM device_data')
    conn.commit()
    conn.close()
    print("Data cleared")
    return render_template('clear_data.html', status="success")


@app.route('/api/clear_data', methods=['POST'])
def clear_data_json():
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM device_data')
    conn.commit()
    conn.close()
    print("Data cleared")
    return jsonify({"status": "success"})


@app.route('/clear_devices', methods=['GET'])
def clear_devices():
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM devices')
    conn.commit()
    conn.close()
    print("Devices cleared")
    return render_template('clear_devices.html', status="success")


@app.route('/api/clear_devices', methods=['POST'])
def clear_devices_json():
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM devices')
    conn.commit()
    conn.close()
    print("Devices cleared")
    return jsonify({"status": "success"})


@app.route('/alive', methods=['GET'])
def alive():
    return jsonify({"status": "alive"})


@app.route('/delete_device/<device_id>', methods=['POST'])
def delete_device(device_id):
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM devices WHERE id = ?', (device_id,))
    conn.commit()
    conn.close()
    print(f"Device {device_id} deleted")
    return render_template('delete_device.html', status="success", device_id=device_id)


@app.route('/api/delete_device/<device_id>', methods=['POST'])
def delete_device_json(device_id):
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM devices WHERE id = ?', (device_id,))
    conn.commit()
    conn.close()
    print(f"Device {device_id} deleted")
    return jsonify({"status": "success"})


@app.route('/clear_data/<device_id>', methods=['POST'])
def clear_data_for_device(device_id):
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM device_data WHERE device_id = ?', (device_id,))
    conn.commit()
    conn.close()
    print(f"Data for device {device_id} cleared")
    return jsonify({"status": "success"})


@app.route('/get_event_file', methods=['GET'])
def get_event_file():
    conn = sqlite3.connect('match.db')
    cursor = conn.cursor()
    cursor.execute('SELECT match_data FROM event')
    data = cursor.fetchall()
    conn.close()
    print(f"Data fetched: {data}")
    return jsonify(data)


@app.route('/post_event_file', methods=['POST'])
def post_match():
    if 'Event' not in request.files:
        return jsonify({"status": "error", "message": "No file provided"}), 400

    file = request.files['Event']
    try:
        data = json.load(file)
    except json.JSONDecodeError:
        return jsonify({"status": "error", "message": "Invalid JSON format"}), 400

    conn = sqlite3.connect('match.db')
    cursor = conn.cursor()

    try:
        for match in data:
            match_id = match.get('key')
            match_data = json.dumps(match)
            cursor.execute('INSERT INTO event (match_id, match_data) VALUES (?, ?)', (match_id, match_data))

        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"{len(data)} matches posted"}), 200
    except Exception as e:
        conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/clear_event_file', methods=['POST'])
def clear_event_data():
    conn = sqlite3.connect('match.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM event')
    conn.commit()
    conn.close()
    print("Event data cleared")
    return jsonify({"status": "success"})


def display_logo():
    logo = r"""
   _____                  __              ____                _____                          
  / ___/_________  __  __/ /_            / __ \____  _____   / ___/___  ______   _____  _____
  \__ \/ ___/ __ \/ / / / __/  ______   / / / / __ \/ ___/   \__ \/ _ \/ ___/ | / / _ \/ ___/
 ___/ / /__/ /_/ / /_/ / /_   /_____/  / /_/ / /_/ (__  )   ___/ /  __/ /   | |/ /  __/ /    
/____/\___/\____/\__,_/\__/            \____/ .___/____/   /____/\___/_/    |___/\___/_/     
                                           /_/                                               

"""
    print(logo)


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return "Unable to get IP Address"


def display_loading():
    print("Starting Scout-Ops Server...", end="", flush=True)
    for _ in range(5):
        time.sleep(0.5)
        print(".", end="", flush=True)
    print("\n")


def signal_handler(sig, frame):
    print("\nGracefully shutting down the server...")
    create_log_folder()
    http_server.stop()
    sys.exit(0)


def create_log_folder():
    log_dir = 'log'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_dir = os.path.join(log_dir, timestamp)
    os.makedirs(backup_dir)

    shutil.move('devices.db', os.path.join(backup_dir, 'devices.db'))
    shutil.move('match.db', os.path.join(backup_dir, 'match.db'))
    print(f"Moved databases to {backup_dir}")


if __name__ == '__main__':
    # Suppress specific warning about using the development server in production
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        warnings.filterwarnings("ignore", category=UserWarning, message='.*server.*')

    # Suppress other unnecessary logs
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # Display the logo and loading screen
    display_logo()
    display_loading()

    # Initialize the database
    init_db()

    # Get and display the local IP address
    local_ip = get_local_ip()
    print(f"Scout-Ops Server is running on: http://{local_ip}:5000\n")

    # Start the server
    http_server = WSGIServer(('0.0.0.0', 5000), app)

    # Register the signal handler for SIGINT
    signal.signal(signal.SIGINT, signal_handler)

    http_server.serve_forever()
