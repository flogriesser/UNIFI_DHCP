import os
import requests
import json
import csv
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

controller_url = os.getenv('UNIFI_CONTROLLER_URL')
username = os.getenv('UNIFI_USERNAME')
password = os.getenv('UNIFI_PASSWORD')

login_url = f'{controller_url}/api/login'
clients_url = f'{controller_url}/api/s/default/stat/sta'
logout_url = f'{controller_url}/logout'

payload = {
    'username': username,
    'password': password
}

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()

# Start a session
session = requests.Session()

# Login to the UniFi Controller
response = session.post(login_url, json=payload, verify=False)

if response.status_code == 200:
    print('Login successful')
else:
    print('Login failed:', response.status_code, response.text)
    exit(1)

# Get all clients
response = session.get(clients_url, verify=False)

if response.status_code == 200:
    clients = response.json()['data']
else:
    print('Failed to retrieve clients:', response.status_code, response.text)
    exit(1)

# Logout
response = session.get(logout_url, verify=False)

if response.status_code == 200:
    print('Logout successful')
else:
    print('Logout failed:', response.status_code, response.text)

# Save to CSV
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
csv_filename = f'clients_{timestamp}.csv'

with open(csv_filename, mode='w', newline='') as csv_file:
    fieldnames = ['timestamp', 'mac', 'ip', 'hostname']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()
    for client in clients:
        writer.writerow({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'mac': client['mac'],
            'ip': client['ip'],
            'hostname': client.get('hostname', 'N/A')
        })

print(f"Client information saved to {csv_filename}")
