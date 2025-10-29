################## GCP VM LABS PRE-REQ == START ##################################################

#!/usr/bin/env bash
# setup-xrdp-xfce.sh
# Ubuntu/Debian: install XFCE, Xubuntu desktop, XRDP; enable SSH password auth; create user; configure XRDP startwm.
# Usage: sudo ./setup-xrdp-xfce.sh
set -euo pipefail
IFS=$'\n\t'

# ---- Configurable defaults ----
DEFAULT_USER="testuser"
DEFAULT_SHELL="/bin/bash"
NO_REBOOT=false   # set true if you don't want script to prompt for reboot when modifying kernel options (not used here)

# ---- Helpers ----
log()    { printf '\e[1;34m[INFO]\e[0m %s\n' "$*"; }
warn()   { printf '\e[1;33m[WARN]\e[0m %s\n' "$*"; }
err()    { printf '\e[1;31m[ERROR]\e[0m %s\n' "$*"; exit 1; }

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    err "This script must be run as root. Use: sudo $0"
  fi
}

apt_update_install() {
  log "Updating apt cache..."
  apt update -y

  log "Installing XFCE, Xubuntu desktop and xrdp (this may take some time)..."
  DEBIAN_FRONTEND=noninteractive apt install -y xfce4 xfce4-goodies xubuntu-desktop xrdp
}

enable_start_service() {
  local svc=$1
  log "Enabling and starting systemd service: $svc"
  systemctl enable --now "$svc"
}

set_ssh_password_auth() {
  # Prefer editing files under /etc/ssh/sshd_config.d if they exist; otherwise edit sshd_config
  local target_dir="/etc/ssh/sshd_config.d"
  local file60="${target_dir}/60-cloudimg-settings.conf"
  local fallback="/etc/ssh/sshd_config"

  if [ -d "$target_dir" ]; then
    log "Ensuring PasswordAuthentication yes in $file60 (creating/updating)"
    if grep -qE '^\s*PasswordAuthentication' "$file60" 2>/dev/null; then
      sed -i 's/^\s*PasswordAuthentication.*/PasswordAuthentication yes/' "$file60"
    else
      echo "PasswordAuthentication yes" >> "$file60"
    fi
  else
    log "Directory $target_dir not found; updating $fallback"
    if grep -qE '^\s*PasswordAuthentication' "$fallback"; then
      sed -i 's/^\s*PasswordAuthentication.*/PasswordAuthentication yes/' "$fallback"
    else
      echo "PasswordAuthentication yes" >> "$fallback"
    fi
  fi

  log "Restarting sshd service to apply changes"
  systemctl restart sshd
}

create_user_and_setup() {
  local username="${1:-$DEFAULT_USER}"
  local shell="${2:-$DEFAULT_SHELL}"

  if id "$username" &>/dev/null; then
    warn "User '$username' already exists — skipping creation."
  else
    log "Creating user: $username"
    adduser --shell "$shell" --disabled-password --gecos "" "$username"
    usermod -aG sudo "$username"
    log "User '$username' created and added to sudo group"
  fi

  # Prompt for password and set it
  log "Set password for user '$username'. You will be prompted to enter a password."
  # Use passwd interactively so it prompts twice for confirmation.
  passwd "$username"
}

configure_xrdp_startwm() {
  # Backup original startwm.sh if exists
  local startwm="/etc/xrdp/startwm.sh"
  if [ -f "$startwm" ]; then
    cp -n "$startwm" "${startwm}.bak.$(date +%s)" || true
  fi

  log "Configuring $startwm to use startxfce4 for XRDP sessions"
  cat > "$startwm" <<'EOF'
#!/bin/sh
# /etc/xrdp/startwm.sh - start XFCE for xrdp sessions
# This script will be executed as the connecting user session
# Ensure PATH is set
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Start XFCE desktop environment
if [ -x /usr/bin/startxfce4 ]; then
  exec startxfce4
fi

# Fallback: try xfce-session
if [ -x /usr/bin/xfce4-session ]; then
  exec xfce4-session
fi

# Last resort: run a shell
exec /bin/sh
EOF

  chmod +x "$startwm"
  log "$startwm written and made executable"

  # Create .xsession for default user(s) or prompt user to create one for a specific user
  log "You can optionally create ~/.xsession containing 'startxfce4' for each user who will log in via XRDP."
  # We'll not write to users' home automatically (except if user exists and we prompt), we will prompt below in the main flow.
}

show_status() {
  log "XRDP service status:"
  systemctl status xrdp --no-pager || true

  log "SSHD service status:"
  systemctl status sshd --no-pager || true
}

# ---- Main ----
require_root

log "Interactive setup for XRDP + XFCE on Debian/Ubuntu"

# 1) Install packages
apt_update_install

# 2) Enable and start xrdp
enable_start_service xrdp

# 3) Ensure SSH allows password authentication and restart
set_ssh_password_auth

# 4) Ask for username to create (default testuser)
read -rp "Enter username to create (default: ${DEFAULT_USER}): " INPUT_USER
USER_TO_CREATE="${INPUT_USER:-$DEFAULT_USER}"

create_user_and_setup "$USER_TO_CREATE"

# 5) Create .xsession in user's home to auto-start XFCE (so XRDP session uses it)
USER_HOME_DIR="$(getent passwd "$USER_TO_CREATE" | cut -d: -f6)"
if [ -d "$USER_HOME_DIR" ]; then
  log "Creating .xsession in $USER_HOME_DIR for user $USER_TO_CREATE"
  su - "$USER_TO_CREATE" -c "echo 'startxfce4' > ~/.xsession && chmod +x ~/.xsession" || warn "Failed to create .xsession in $USER_HOME_DIR"
else
  warn "Home directory for $USER_TO_CREATE not found; skipping ~/.xsession creation"
fi

# 6) Configure /etc/xrdp/startwm.sh to start xfce
configure_xrdp_startwm

# 7) Restart xrdp to ensure config applied
log "Restarting xrdp service..."
systemctl restart xrdp

# 8) Display status
show_status


exit 0
################## GCP VM LABS PRE-REQ == END ##################################################
