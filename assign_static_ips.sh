#!/bin/bash

# Load environment variables from .env file
set -a
source .env
set +a

# Function to send a Telegram alert
send_telegram_alert() {
    local message=$1
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" -d chat_id=${TELEGRAM_CHAT_ID} -d text="${message}" > /dev/null
}

# Make a backup of Clients.conf
cp ${CLIENTS_CONF} ${BACKUP_CONF}

# Run the Python script
python3 ${PYTHON_SCRIPT} >> ${LOG_FILE} 2>&1
if [ $? -ne 0 ]; then
    send_telegram_alert "Error: Python script failed. See log for details."
    exit 1
fi

# Restart the isc-dhcp-server service
systemctl restart isc-dhcp-server >> ${LOG_FILE} 2>&1
if [ $? -ne 0 ]; then
    # Restore the backup if restart fails
    cp ${BACKUP_CONF} ${CLIENTS_CONF}
    systemctl restart isc-dhcp-server >> ${LOG_FILE} 2>&1
    if [ $? -ne 0 ]; then
        send_telegram_alert "Error: isc-dhcp-server restart failed. Clients.conf restored. See log for details."
        exit 1
    fi
    send_telegram_alert "Warning: isc-dhcp-server restart failed initially. Restored Clients.conf and restarted successfully."
else
    send_telegram_alert "Success: isc-dhcp-server restarted successfully after updating Clients.conf."
fi
