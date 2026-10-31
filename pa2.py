import xml.etree.ElementTree as ET
import yaml
import json
import sys
from pathlib import Path

class AuditError(Exception):
    """Custom exception for fleet audit errors"""
    

def version_tuple(version, target_length):
    #split the version # into individual numbers and convert them to integers
    parts = tuple(map(int, version.split(".")))
    
    #add zero
    padding = target_length - len(parts)
    return parts + (0,) * padding

def main(xml_file, policy_file):
    """Run the fleet compliance auditor"""
    
    #check if the xml inventory file exists
    if not Path(xml_file).is_file():
        raise AuditError(f"XML file not found: {xml_file}")
    
    #read and parse the xml file
    tree = ET.parse(xml_file)
    #try:
    #    tree = ET.parse(xml_file)
    #except ET.ParseError as error:
    #    raise AuditError(f"Invalid XML file: {error}")
    root = tree.getroot()
    
    #get site name from the xml root element
    site = root.get("site")
    
    #print("Site:", site)
    
    #check if the yaml policy exists
    if not Path(policy_file).is_file():
        raise AuditError(f"Policy file not found: {policy_file}")
    
    #open the yaml file and safely load its policy settings
    with open(policy_file, "r") as file:
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
    violations = []
    compliant = []
    
    #loop through every device element in the xml file
    for device in root.findall("device"):
        #get the value of the id attribute for the current device
        device_id = device.get("id")
        role = device.get("role")
        os_version = device.get("os")
        owner = device.findtext("owner")
        
        #if the device has an id, count it and inspect its interfaces
        if device_id is not None:
            #policy["min_os"]
            #print(device_id, role, os_version)
            
            #count the device under its assigned role
            roles[role] = roles.get(role, 0) + 1
            total_devices += 1
            
            #reset the down interface counter for each device
            down_count = 0
            
            #check each interface under this device
            for intf in device.findall("interface"):
                
                #get the current interface status
                status = intf.get("status")
            
            #count interfaces based on their status
                if status == "up":
                   interfaces["up"] += 1    
                elif status == "down":
                   interfaces["down"] += 1
                   down_count += 1
                else:
                    #include statuses of type other
                   interfaces["other"] += 1
                   
            #check if min_os exists before accessing it 
            if "min_os" in policy and role not in policy["min_os"]:
                violations.append({
                    "device" : device_id,
                    "type" : "unknown_role",
                    "role" : role
                })
            
            #check if the device has a owner
            if owner is None or owner.strip() == "":
                violations.append({
                    "device" : device_id,
                    "type" : "missing_owner"
                })
            
            #check if the device exceeds the allowed number of down interfaces as specified in the policy    
            if "max_down_interfaces" in policy:
                if down_count > policy["max_down_interfaces"]:
                    violations.append({
                    "device": device_id,
                    "type": "too_many_down",
                    "down": down_count
                    })
            #check if the installed os version aginst the minimum requirtment version for each device role
            if "min_os" in policy and role in policy["min_os"]:
                required_version = policy["min_os"][role]
                
                #make both version the same length before comparing them
                target_length = max(len(os_version.split(".")), len(required_version.split(".")))
                
                #convert both versions into numeric tuples
                installed = version_tuple(os_version, target_length)
                required = version_tuple(required_version, target_length)
                
                #compare installed os againsit required os and add a violation if it does violate it
                if installed < required:
                    violations.append({
                        "device": device_id,
                        "type": "os_outdated",
                        "found": os_version,
                        "required": required_version
                        })
            
            #add the device complaint list if it has no violations
            if not any(v["device"] == device_id for v in violations):
                compliant.append(device_id)
                    
        else:
            #count devices that are missing an id
            skipped_devices += 1
    
    #sort the complaint device ids alphabetically
    compliant.sort()
    
    #build the report using the information above
    report = {
        "site": site,
        "total_devices" : total_devices,
        "skipped_devices" : skipped_devices,
         "roles" : roles,
         "interfaces" : interfaces,
         "violations" : violations,
         "compliant" : compliant
    }
    
    #display the report in a json format
    print(json.dumps(report, indent= 4))
    #print(report)     
    #print(roles)
    #print(interfaces)
    #print("Total devices:", total_devices)
    #print("Skipped devices:", skipped_devices)
    
    #save the report to audit.json in the current directory
    with open("audit.json", "w")  as file:
        json.dump(report, file, indent= 4)
    
#only run the program when this file is executed pa2.py
if __name__ == "__main__":
    
    #check if the two command line arguments were provided
    if len(sys.argv) != 3:
        
        #print the correct command format and exit with an error code
        print("Usage: python pa2.py DEVICES.xml POLICY.yaml")
        sys.exit(1)
    else:
        #run the audit using the supplied xml and ymal files names
        try:
            main(sys.argv[1], sys.argv[2])
        #use the custom audit error to print a readable error message
        except AuditError as error:
            print(f"Error: {error}")
            sys.exit(1)