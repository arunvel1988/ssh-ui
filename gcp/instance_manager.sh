#!/bin/bash

echo "=============================="
echo " GCP Instance Bulk Manager"
echo "=============================="

read -p "Enter instance name prefix (default: kubernetes-): " PREFIX
PREFIX=${PREFIX:-kubernetes-}

echo
echo "Fetching instances with name starting with '$PREFIX' ..."
echo

# Fetch Name | Zone | Status
INSTANCES=$(gcloud compute instances list \
  --filter="name~'^$PREFIX.*'" \
  --format="value(name,zone,status)")

if [[ -z "$INSTANCES" ]]; then
  echo "No instances found with prefix '$PREFIX'"
  exit 1
fi

echo "Found instances:"
echo "--------------------------------------------------"
printf "%-35s %-20s %-12s\n" "INSTANCE_NAME" "ZONE" "STATUS"
echo "--------------------------------------------------"

echo "$INSTANCES" | while read -r NAME ZONE STATUS; do
  printf "%-35s %-20s %-12s\n" "$NAME" "$ZONE" "$STATUS"
done

echo "--------------------------------------------------"
echo

echo "Choose an action:"
echo "1) Start instances (only TERMINATED)"
echo "2) Stop instances (only RUNNING)"
echo "3) Delete instances (any state)"
read -p "Enter choice [1-3]: " ACTION

echo
read -p "Are you sure? This will apply to all applicable instances (yes/no): " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
  echo "Operation cancelled"
  exit 1
fi

echo

# Process instances based on status
while read -r NAME ZONE STATUS; do
  case $ACTION in
    1)
      if [[ "$STATUS" == "TERMINATED" ]]; then
        echo "Starting $NAME in $ZONE"
        gcloud compute instances start "$NAME" --zone="$ZONE"
      else
        echo "Skipping $NAME (status: $STATUS)"
      fi
      ;;
    2)
      if [[ "$STATUS" == "RUNNING" ]]; then
        echo "Stopping $NAME in $ZONE"
        gcloud compute instances stop "$NAME" --zone="$ZONE"
      else
        echo "Skipping $NAME (status: $STATUS)"
      fi
      ;;
    3)
      echo "Deleting $NAME in $ZONE"
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
