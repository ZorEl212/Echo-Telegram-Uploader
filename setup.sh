#!/bin/bash

# Variables
SERVICE_NAME="tup-daemon"
SCRIPT_PATH="/usr/bin/tup-daemon"  
USERNAME=$USER  
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
CONFIG_FILE="$HOME/.tup/config.ini"

# Check if config.ini already exists
if [ -f "${CONFIG_FILE}" ]; then
    echo "Using existing config file: ${CONFIG_FILE}"
else
    echo "Please enter the following information for your Telegram bot:"
    read -p "API ID: " API_ID
    read -p "API Hash: " API_HASH
    read -p "Bot Token: " BOT_TOKEN
    read -p "Group Chat ID: " GROUP_CHAT_ID

    CONFIG_DIR=$(dirname "${CONFIG_FILE}")
    mkdir -p "${CONFIG_DIR}"

    # Create the configuration file
    cat > "${CONFIG_FILE}" <<EOF
[telegram]
api_id = ${API_ID}
api_hash = ${API_HASH}
bot_token = ${BOT_TOKEN}
session_path = ${HOME}/.tup  # default session path
group_chat_id = ${GROUP_CHAT_ID}
EOF
fi

# Copy scripts and set permissions (assuming they are already in place)
sudo cp tup-daemon.py ${SCRIPT_PATH}
sudo cp tup-cli.py /usr/bin/tup-cli
sudo chmod +x /usr/bin/tup-cli
sudo chmod +x ${SCRIPT_PATH}

# Create the service file
sudo cat > ${SERVICE_FILE} <<EOF
[Unit]
Description=Echo Telegram uploader bot
After=network.target

[Service]
User=${USERNAME}
WorkingDirectory=$(dirname "${SCRIPT_PATH}")
ExecStart=${SCRIPT_PATH}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo chmod 644 ${SERVICE_FILE}
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl start ${SERVICE_NAME}
sudo systemctl status ${SERVICE_NAME}
