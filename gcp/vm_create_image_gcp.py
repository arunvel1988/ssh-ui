from googleapiclient import discovery
from google.auth import default
import sys

def read_config():
    config = {}
    with open("cloud.txt") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                config[k] = v
    return config

def main():
    config = read_config()
    project_id = config["PROJECT_ID"]

    credentials, _ = default()
    compute = discovery.build("compute", "v1", credentials=credentials)

    stopped_vms = []

    zones = compute.zones().list(project=project_id).execute()["items"]

    for zone in zones:
        zone_name = zone["name"]

        resp = compute.instances().list(
            project=project_id,
            zone=zone_name
        ).execute()

        for inst in resp.get("items", []):
            if inst["status"] != "TERMINATED":
                continue

            boot_disk = None
            for d in inst["disks"]:
                if d.get("boot"):
                    boot_disk = d["source"].split("/")[-1]

            if boot_disk:
                stopped_vms.append({
                    "name": inst["name"],
                    "zone": zone_name,
                    "disk": boot_disk
                })

    if not stopped_vms:
        print("No stopped instances found.")
        sys.exit(0)

    print("\nStopped instances:\n")
    for i, vm in enumerate(stopped_vms, start=1):
        print(f"{i}. {vm['name']} | zone={vm['zone']} | boot_disk={vm['disk']}")

    choice = input("\nSelect instance number (or 'q' to quit): ").strip()

    if choice.lower() == "q":
        print("Exiting without creating image.")
        sys.exit(0)

    if not choice.isdigit() or not (1 <= int(choice) <= len(stopped_vms)):
        print("Invalid selection.")
        sys.exit(1)

    vm = stopped_vms[int(choice) - 1]

    image_name = input(
        f"\nEnter image name for VM '{vm['name']}': "
    ).strip()

    if not image_name:
        print("Image name cannot be empty.")
        sys.exit(1)

    confirm = input(
        f"\nCreate image '{image_name}' from VM '{vm['name']}'? (yes/no): "
    ).strip().lower()

    if confirm != "yes":
        print("Operation cancelled.")
        sys.exit(0)

    compute.images().insert(
        project=project_id,
        body={
            "name": image_name,
            "sourceDisk": f"projects/{project_id}/zones/{vm['zone']}/disks/{vm['disk']}"
        }
    ).execute()

    print("\nImage creation request submitted successfully.")
    print(f"Image name : {image_name}")
    print(f"Source VM  : {vm['name']}")
    print(f"Zone       : {vm['zone']}")

if __name__ == "__main__":
    main()
