#!/bin/bash
# Puppet Master Setup

set -e

# ==== IPs & hostnames ====
MASTER_IP="192.168.56.3"
MASTER_HOSTNAME="puppet-master"
AGENT1_IP="192.168.56.4"
AGENT1_HOSTNAME="puppet-agent-1"
AGENT2_IP="192.168.56.5"
AGENT2_HOSTNAME="puppet-agent-2"

# Update /etc/hosts
sudo tee /etc/hosts > /dev/null <<EOL
127.0.0.1 localhost
$MASTER_IP $MASTER_HOSTNAME
$AGENT1_IP $AGENT1_HOSTNAME
$AGENT2_IP $AGENT2_HOSTNAME
EOL

# Install dependencies
sudo apt update
sudo apt install -y wget curl lsb-release gnupg

# Add Puppet repo
wget https://apt.puppet.com/puppet8-release-jammy.deb
sudo dpkg -i puppet8-release-jammy.deb
sudo apt update

# Install Puppet Server
sudo apt install -y puppetserver

# Reduce JVM memory for lab
sudo sed -i 's/^JAVA_ARGS=.*/JAVA_ARGS="-Xms512m -Xmx512m"/' /etc/default/puppetserver

# Stop Puppet Server
sudo systemctl stop puppetserver || true

# Clean old CA/SSL
sudo rm -rf /etc/puppetlabs/puppetserver/ca /etc/puppetlabs/puppet/ssl
sudo rm -rf /etc/puppetlabs/puppet/cache

# Setup CA
sudo /opt/puppetlabs/bin/puppetserver ca setup

# Set OpenSSL environment for Puppet Server
sudo systemctl stop puppetserver
sudo mkdir -p /etc/systemd/system/puppetserver.service.d
echo -e "[Service]\nEnvironment=\"OPENSSL_CONF=/opt/puppetlabs/puppet/ssl/openssl.cnf\"" | \
  sudo tee /etc/systemd/system/puppetserver.service.d/openssl.conf
sudo systemctl daemon-reexec

# Start Puppet Server
sudo systemctl enable --now puppetserver

# Verify CA
sudo OPENSSL_CONF=/opt/puppetlabs/puppet/ssl/openssl.cnf \
  /opt/puppetlabs/bin/puppetserver ca list --all || true

echo "Puppet Master setup complete."
