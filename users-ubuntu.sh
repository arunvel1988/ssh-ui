#!/usr/bin/env bash
# create_users.sh
# Creates users: <prefix>-user1 .. <prefix>-userN
# Password for each user is the same as the username.
# Adds each user to the sudo group.
set -euo pipefail

# Ensure script runs as root
if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root (use sudo)." >&2
  exit 1
fi

# Read and sanitize company prefix
read -r -p "Enter company prefix (e.g. tcs): " prefix_raw
if [[ -z "$prefix_raw" ]]; then
  echo "Prefix cannot be empty." >&2
  exit 1
fi

# sanitize: lowercase, replace non-alnum with '-', collapse multiple '-' and trim leading/trailing '-'
prefix=$(echo "$prefix_raw" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//')
if [[ -z "$prefix" ]]; then
  echo "Prefix became empty after sanitization. Use a different prefix." >&2
  exit 1
fi

# Read number of users
read -r -p "How many users do you want to create? (e.g. 10): " count_raw
if ! [[ "$count_raw" =~ ^[0-9]+$ ]]; then
  echo "Please enter a positive integer for the number of users." >&2
  exit 1
fi
count=$((count_raw))
if [[ $count -le 0 ]]; then
  echo "Number of users must be greater than zero." >&2
  exit 1
fi

# Optional: choose starting index (default 1)
read -r -p "Starting number (default 1): " start_raw
if [[ -z "$start_raw" ]]; then
  start=1
else
  if ! [[ "$start_raw" =~ ^[0-9]+$ ]]; then
    echo "Starting number must be an integer." >&2
    exit 1
  fi
  start=$((start_raw))
  if [[ $start -le 0 ]]; then
    echo "Starting number must be >= 1" >&2
    exit 1
  fi
fi

echo
echo "Will create $count users with prefix: $prefix"
echo "Usernames will be: ${prefix}-user${start} .. ${prefix}-user$((start + count - 1))"
read -r -p "Proceed? [y/N]: " confirm
if [[ "${confirm,,}" != "y" && "${confirm,,}" != "yes" ]]; then
  echo "Aborted by user."
  exit 0
fi

created=0
skipped=0

for ((i=0; i<count; i++)); do
  num=$((start + i))
  username="${prefix}-user${num}"
  password="$username"

  if id -u "$username" &>/dev/null; then
    echo "[SKIP] User $username already exists."
    skipped=$((skipped+1))
    continue
  fi

  # Create user with home directory and bash shell
  useradd -m -s /bin/bash -c "${prefix} user ${num}" "$username"
  # Set password (username:password)
  echo "${username}:${password}" | chpasswd

  # Force password change on first login? Uncomment if you want that:
  # chage -d 0 "$username"

  # Add to sudo group (works on Debian/Ubuntu)
  usermod -aG sudo "$username"

  # Optional: lock password? (not requested)
  # passwd -e "$username"

  echo "[OK] Created $username (password: $password) and added to sudo group."
  created=$((created+1))
done

echo
echo "Done. Created: $created, Skipped (already existed): $skipped"
echo "Note: passwords are the same as usernames. Consider forcing password change on first login:"
echo "  sudo chage -d 0 <username>"
