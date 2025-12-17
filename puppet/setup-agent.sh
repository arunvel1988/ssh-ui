#!/bin/bash
# Puppet Agent Setup

set -e

# ==== IPs & hostnames ====
MASTER_IP="192.168.56.10"
MASTER_HOSTNAME="puppet-master"

AGENT1_IP="192.168.56.11"
AGENT1_HOSTNAME="puppet-agent-1"

AGENT2_IP="192.168.56.12"
AGENT2_HOSTNAME="puppet-agent-2"

AGENT_IP=$(hostname -I | awk '{print $1}')
AGENT_HOSTNAME=$(hostname)

# Update /etc/hosts
sudo tee /etc/hosts > /dev/null <<EOL
127.0.0.1 localhost
$MASTER_IP $MASTER_HOSTNAME
$AGENT1_IP $AGENT1_HOSTNAME
$AGENT2_IP $AGENT2_HOSTNAME
$AGENT_IP $AGENT_HOSTNAME
EOL

# Install dependencies
sudo apt update
sudo apt install -y wget curl lsb-release gnupg

# Add Puppet repo
wget https://apt.puppet.com/puppet8-release-jammy.deb
sudo dpkg -i puppet8-release-jammy.deb
sudo apt update

# Install Puppet Agent
sudo apt install -y puppet-agent

# Configure Puppet server
sudo /opt/puppetlabs/bin/puppet config set server $MASTER_HOSTNAME --section main

# Enable Puppet agent service
sudo systemctl enable --now puppet

# Request certificate from Puppet Master
sudo /opt/puppetlabs/bin/puppet agent -t || true

echo "Puppet Agent setup complete."
