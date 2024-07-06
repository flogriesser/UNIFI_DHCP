import os
import requests
import json
import csv
from datetime import datetime, timedelta
from ipaddress import ip_address
from dotenv import load_dotenv

def update_clients():
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
        return

    # Get all clients
    response = session.get(clients_url, verify=False)

    if response.status_code == 200:
        clients = response.json()['data']
    else:
        print('Failed to retrieve clients:', response.status_code, response.text)
        return

    # Logout
    response = session.get(logout_url, verify=False)

    if response.status_code == 200:
        print('Logout successful')
    else:
        print('Logout failed:', response.status_code, response.text)

    # Define the CSV filename
    csv_filename = 'clients.csv'
    current_time = datetime.now()
    one_week_ago = current_time - timedelta(weeks=1)

    # Read the existing CSV file
    existing_clients = {}
    if os.path.exists(csv_filename):
        with open(csv_filename, mode='r', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                mac = row['mac']
                timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                ip_address = row['ip']
                if timestamp > one_week_ago:
                    existing_clients[mac] = {'timestamp': timestamp, 'mac': mac, 'ip': ip_address, 'hostname': row['hostname']}

    # Update or add clients
    for client in clients:
        mac = client['mac']
        ip = client.get('ip', 'N/A')
        hostname = client.get('hostname', 'N/A')
        timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')

        if mac in existing_clients:
            existing_clients[mac]['timestamp'] = timestamp
        else:
            existing_clients[mac] = {'timestamp': timestamp, 'mac': mac, 'ip': ip, 'hostname': hostname}

    # Write the updated clients back to the CSV file
    with open(csv_filename, mode='w', newline='') as csv_file:
        fieldnames = ['timestamp', 'mac', 'ip', 'hostname']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        for client in existing_clients.values():
            writer.writerow(client)

    print(f"Client information updated in {csv_filename}")

def create_clients_conf():
    # Load environment variables from .env file
    load_dotenv()

    start_ip = ip_address(os.getenv('START_IP'))
    end_ip = ip_address(os.getenv('END_IP'))
    csv_filename = '/etc/dhcp/clients.csv'
    conf_filename = '/etc/dhcp/Clients.conf'

    # Function to generate the next IP address in the range
    def next_ip(current_ip):
        next_ip = current_ip + 1
        if next_ip > end_ip:
            raise ValueError("Ran out of IP addresses in the specified range")
        return next_ip

    # Read the CSV file
    clients = []
    if os.path.exists(csv_filename):
        with open(csv_filename, mode='r', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                clients.append(row)

    # Assign IP addresses and create the Clients.conf entries
    assigned_ips = set()
    current_ip = start_ip
    conf_entries = []

    for client in clients:
        mac = client['mac']
        ip_address_str = client['ip']

        if mac == 'N/A':  # Skip clients with invalid MAC addresses
            continue

        if ip_address_str == 'N/A':
            while str(current_ip) in assigned_ips:
                current_ip = next_ip(current_ip)
            ip_address_str = str(current_ip)
            client['ip'] = ip_address_str
            assigned_ips.add(ip_address_str)
            current_ip = next_ip(current_ip)
        else:
            assigned_ips.add(ip_address_str)

        hostname = f"client_{ip_address_str.replace('.', '_')}"

        conf_entries.append(f'host {hostname} {{')
        conf_entries.append(f'    hardware ethernet {mac};')
        conf_entries.append(f'    fixed-address {ip_address_str};')
        conf_entries.append(f'}}\n')

    # Write the Clients.conf file
    with open(conf_filename, mode='w') as conf_file:
        conf_file.write('\n'.join(conf_entries))

    # Update the CSV with assigned IP addresses
    with open(csv_filename, mode='w', newline='') as csv_file:
        fieldnames = ['timestamp', 'mac', 'ip', 'hostname']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        for client in clients:
            writer.writerow(client)

    print(f"Clients.conf created with {len(clients)} entries")

# Call the functions
update_clients()
create_clients_conf()
