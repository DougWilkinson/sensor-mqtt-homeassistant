import config
import json
import httpclient
import machine

def version():
    return "1"

def save_file(file, version):
    fullname = file + version + ".py"
    try:
        response = http.get(baseURL + fullname, saveToFile=fullname)
        assert(response.status_code == 200)
        print("Received: ",fullname)
        return True
    except:
        print("Http error: ", response.status_code)
        return False

def getjson(file):
    try:
        return http.get(baseURL+file).json()
    except:
        return None

def save_json(file, data):
    try:
        f = open(file, 'w')
        f.write(json.dumps(data))
        f.close()
        return True
    except:
        print("Save failed.")
        return False

def save_primary():
    print("Saving desired to primary config")
    return save_json(config.espMAC,desired)

def save_alternate():
    print("Saving current to alternate config")
    return save_json(config.espMAC+".alt",config.current)

# Query HASS for update files

print("Clearing update flags ...")
config.clear('update')
config.clear('update_failed')

http = httpclient.HttpClient()
baseURL = "http://192.168.1.138:8123/local/code/"

desired = getjson(config.espMAC)
latest = getjson("latestversions")

if desired is None or latest is None:
    config.set('server_failure')
    config.reboot()

failedfiles = []

for file in desired:
    skip=False
    print("Item: ",file, "ver: ", desired[file])
    if file == "name":
        print("Skipping name")
        skip = True

    if desired[file] == "latest":
        if file in latest:
            desired[file] = latest[file]
        else:
            print("! Desired file not in latest list: ",file)
            failedfiles.append(desired[file] + file)
            skip = True

    #skip if config.current matches desired
    if file in config.current:
        if config.current[file] == desired[file]:
            skip = True
            print("Versions match, skipping ",file)

    if not skip:
        if not save_file(file,desired[file]):
            failedfiles.append(desired[file] + file)

if len(failedfiles) > 0:
    print("Update failed ...")
    config.set('update_failed')
    print("Unable to get files: \n",failedfiles)
    print("Saving in failedfiles")
    try:
        with open('failedfiles','w') as f:
            for file in failedfiles:
                f.write(file + "\n")
            f.close()
    except:
        print("Could not save failedfiles ...")
    config.reboot()

# Update successful, save primary-->Alternate and update primary

print("Attempting save for new configs ...")

if not save_alternate() or not save_primary():
    print("Config save failed!")
    config.set('update_failed')

config.reboot()
