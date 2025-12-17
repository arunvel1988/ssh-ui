#!/bin/bash
# Puppet 8 Server Full Setup for Ubuntu 22.04 (Jammy)

set -e

# 1. Install dependencies
sudo apt update
sudo apt install -y wget curl lsb-release gnupg

# 2. Add Puppet 8 repository
wget https://apt.puppet.com/puppet8-release-jammy.deb
sudo dpkg -i puppet8-release-jammy.deb
sudo apt update

# 3. Install Puppet Server
sudo apt install -y puppetserver

# 4. Configure JVM memory for lab environment (optional)
sudo sed -i 's/^JAVA_ARGS=.*/JAVA_ARGS="-Xms512m -Xmx512m"/' /etc/default/puppetserver

# 5. Ensure hostname resolution
HOSTNAME_FQDN=$(hostname -f)
sudo sed -i "/puppet-master/d" /etc/hosts
echo "127.0.0.1 puppet $HOSTNAME_FQDN" | sudo tee -a /etc/hosts

# 6. Stop Puppet Server if running
sudo systemctl stop puppetserver || true

# 7. Remove existing CA and SSL files (clean slate)
sudo rm -rf /etc/puppetlabs/puppetserver/ca /etc/puppetlabs/puppet/ssl
sudo rm -rf /etc/puppetlabs/puppet/cache

# 8. Generate new CA
sudo /opt/puppetlabs/bin/puppetserver ca setup

# 9. Configure Puppet Server to use bundled OpenSSL
sudo systemctl stop puppetserver
sudo mkdir -p /etc/systemd/system/puppetserver.service.d
echo -e "[Service]\nEnvironment=\"OPENSSL_CONF=/opt/puppetlabs/puppet/ssl/openssl.cnf\"" | \
  sudo tee /etc/systemd/system/puppetserver.service.d/openssl.conf
sudo systemctl daemon-reexec

# 10. Start Puppet Server
sudo systemctl enable --now puppetserver

# 11. Verify Puppet CA
sudo OPENSSL_CONF=/opt/puppetlabs/puppet/ssl/openssl.cnf \
  /opt/puppetlabs/bin/puppetserver ca list --all

echo "Puppet 8 Server setup complete. CA is functional."
