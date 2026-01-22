import sys
from googleapiclient import discovery
from google.auth import default

def read_config(file_path="cloud.txt"):
    config = {}
    with open(file_path, "r") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                config[key] = value
    return config

def start_stop_vms(action):
    if action not in ("start", "stop"):
        print("Usage: python vm_start_stop.py start|stop")
        sys.exit(1)

    config = read_config()

    project_id = config["PROJECT_ID"]
    label_key = config["LABEL_KEY"]
    label_value = config["LABEL_VALUE"]

    credentials, _ = default()
    compute = discovery.build("compute", "v1", credentials=credentials)

    zones = compute.zones().list(project=project_id).execute().get("items", [])

    for zone in zones:
        zone_name = zone["name"]

        instances = compute.instances().list(
            project=project_id,
            zone=zone_name,
            filter=f"labels.{label_key}={label_value}"
        ).execute().get("items", [])

        for instance in instances:
            name = instance["name"]
            status = instance["status"]

            if action == "start" and status == "TERMINATED":
                compute.instances().start(
                    project=project_id,
                    zone=zone_name,
                    instance=name
                ).execute()
                print(f"STARTED: {name} ({zone_name})")

            elif action == "stop" and status == "RUNNING":
                compute.instances().stop(
                    project=project_id,
                    zone=zone_name,
                    instance=name
                ).execute()
                print(f"STOPPED: {name} ({zone_name})")

            else:
                print(f"SKIPPED: {name} ({zone_name}) - state={status}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python vm_start_stop.py start|stop")
        sys.exit(1)

    start_stop_vms(sys.argv[1])
