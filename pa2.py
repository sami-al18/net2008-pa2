import xml.etree.ElementTree as ET
import yaml
import json

def main():
    """Run the fleet compliance auditor"""
    tree = ET.parse("PA2_sample1.xml")
    root = tree.getroot()
    site = root.get("site")
    
    #print("Site:", site)
    
    with open("PA2_policy.yaml", "r") as file:
        policy = yaml.safe_load(file)
    
    #store counts by device role
    roles = {}
    
    #track the number of interface in each status section
    interfaces = {
        "up": 0,
        "down": 0,
        "other": 0
    }
    
    #counters for report summary
    total_devices = 0
    skipped_devices = 0
    
    #loop through every device element in the xml file
    for device in root.findall("device"):
        #get the value of the id attribute fro the current device
        device_id = device.get("id")
        role = device.get("role")
        os_version = device.get("os")
        
        #if the device has an id, count it and inspect its interfaces
        if device_id is not None:
            #print(device_id, role, os_version)
            roles[role] = roles.get(role, 0) + 1
            total_devices += 1
            
            #check each interface under the device
            for intf in device.findall("interface"):
                status = intf.get("status")
            
            #count interfaces based on their status
                if status == "up":
                   interfaces["up"] += 1    
                elif status == "down":
                   interfaces["down"] += 1
                else:
                   interfaces["other"] += 1
        else:
            #count devices that are missing an id
            skipped_devices += 1
            
    report = {
        "site": site,
        "total_devices" : total_devices,
        "skipped_devices" : skipped_devices,
         "roles" : roles,
         "interfaces" : interfaces,
         "violations" : [],
         "compliant" : []
    }
    
    #display report
    print(json.dumps(report, indent= 4))
    #print(report)     
    #print(roles)
    #print(interfaces)
    #print("Total devices:", total_devices)
    #print("Skipped devices:", skipped_devices)
    
    #save the report
    with open("audit.json", "w")  as file:
        json.dump(report, file, indent= 4)
    
#run main only when this file is executed
if __name__ == "__main__":
    main()
    