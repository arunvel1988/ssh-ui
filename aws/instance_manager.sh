#!/bin/bash

echo "=============================="
echo " AWS EC2 Bulk Instance Manager"
echo "=============================="

# Ask for instance name prefix
read -p "Enter EC2 Name tag prefix (default: kubernetes-): " PREFIX
PREFIX=${PREFIX:-kubernetes-}

echo
echo "Finding RUNNING EC2 instances with Name starting with '$PREFIX' ..."
echo

# Fetch instances: InstanceId Name AZ
INSTANCES=$(aws ec2 describe-instances \
  --filters \
    "Name=instance-state-name,Values=running" \
    "Name=tag:Name,Values=${PREFIX}*" \
  --query 'Reservations[].Instances[].[
      InstanceId,
      Tags[?Key==`Name`].Value | [0],
      Placement.AvailabilityZone
  ]' \
  --output text)

if [[ -z "$INSTANCES" ]]; then
  echo "❌ No running instances found with prefix '$PREFIX'"
  exit 1
fi

echo "Found instances:"
echo "----------------"
printf "%-20s %-30s %-15s\n" "INSTANCE_ID" "NAME" "AZ"
echo "$INSTANCES"
echo "----------------"
echo

# Menu
echo "Choose an action:"
echo "1) Start instances"
echo "2) Stop instances"
echo "3) Terminate instances"
read -p "Enter choice [1-3]: " ACTION

echo
read -p "Are you sure? This will apply to ALL listed instances (yes/no): " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
  echo "Operation cancelled"
  exit 1
fi

echo

# Collect instance IDs
INSTANCE_IDS=$(echo "$INSTANCES" | awk '{print $1}')

case $ACTION in
  1)
    aws ec2 start-instances --instance-ids $INSTANCE_IDS
    ;;
  2)
    aws ec2 stop-instances --instance-ids $INSTANCE_IDS
    ;;
  3)
    aws ec2 terminate-instances --instance-ids $INSTANCE_IDS
    ;;
  *)
    echo "Invalid option"
    exit 1
    ;;
esac

echo
echo "Operation completed"
