import sys
import boto3

def read_config(file_path="cloud.txt"):
    config = {}
    with open(file_path, "r") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                config[key] = value
    return config

def start_stop_instances(action):
    if action not in ("start", "stop"):
        print("Usage: python aws_vm_start_stop.py start|stop")
        sys.exit(1)

    config = read_config()

    region = config["REGION"]
    tag_key = config["TAG_KEY"]
    tag_value = config["TAG_VALUE"]

    ec2 = boto3.client("ec2", region_name=region)

    filters = [
        {"Name": f"tag:{tag_key}", "Values": [tag_value]}
    ]

    response = ec2.describe_instances(Filters=filters)

    instance_ids = []
    instance_states = {}

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instance_ids.append(instance["InstanceId"])
            instance_states[instance["InstanceId"]] = instance["State"]["Name"]

    if not instance_ids:
        print("No matching instances found.")
        return

    if action == "start":
        to_start = [i for i in instance_ids if instance_states[i] == "stopped"]
        if to_start:
            ec2.start_instances(InstanceIds=to_start)
            for i in to_start:
                print(f"STARTED: {i}")
        else:
            print("No instances to start.")

    else:
        to_stop = [i for i in instance_ids if instance_states[i] == "running"]
        if to_stop:
            ec2.stop_instances(InstanceIds=to_stop)
            for i in to_stop:
                print(f"STOPPED: {i}")
        else:
            print("No instances to stop.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python aws_vm_start_stop.py start|stop")
        sys.exit(1)

    start_stop_instances(sys.argv[1])
