#!/bin/bash

echo "=============================="
echo " GCP Instance Bulk Manager"
echo "=============================="

# Ask for prefix
read -p "Enter instance name prefix (default: kubernetes-): " PREFIX
PREFIX=${PREFIX:-kubernetes-}

echo
echo "Finding RUNNING instances starting with '$PREFIX' ..."
echo

# Get instances (name zone)
INSTANCES=$(gcloud compute instances list \
  --filter="name~'^$PREFIX.*' AND status=RUNNING" \
  --format="value(name,zone)")

if [[ -z "$INSTANCES" ]]; then
  echo "No running instances found with prefix '$PREFIX'"
  exit 1
fi

echo "Found instances:"
echo "----------------"
echo "$INSTANCES"
echo "----------------"
echo

# Menu
echo "Choose an action:"
echo "1) Start instances"
echo "2) Stop instances"
echo "3) Delete instances"
read -p "Enter choice [1-3]: " ACTION

echo
read -p "Are you sure? This will apply to ALL listed instances (yes/no): " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
  echo "Operation cancelled"
  exit 1
fi

echo

# Loop through instances
while read -r NAME ZONE; do
  echo "Processing $NAME in $ZONE"

  case $ACTION in
    1)
      gcloud compute instances start "$NAME" --zone="$ZONE"
      ;;
    2)
      gcloud compute instances stop "$NAME" --zone="$ZONE"
      ;;
    3)
      gcloud compute instances delete "$NAME" --zone="$ZONE" --quiet
      ;;
    *)
      echo "Invalid option"
      exit 1
      ;;
  esac
done <<< "$INSTANCES"

echo
echo "Operation completed"
