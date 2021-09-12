import config
import json
import httpclient
import machine
import uos

config.set('update_result', 200)

def version():
    return "15" xx
    # 15: update = 1 check if file already exists if switching "nodenames"
    #     update = 11 overwrite all files even if they exist?

http = httpclient.HttpClient()

def getjson(file):
    try:
        return http.get(config.secrets.code_url+file).json()
    except:
        return None

def save_file(file, version):
    if version[0] == "!":
        getname = file + version.lstrip("!") + ".py"
        savename = file + ".py"
    else:
        getname = file + version + ".py"
        savename = getname
    try:
        response = http.get(config.secrets.code_url + getname, saveToFile=savename)
        assert(response.status_code == 200)
        print("Saved {} as {} ".format(getname,savename))
        return True
    except:
        print("Http error code {} getting {}: ".format(response.status_code,getname))
        return False

def save_json(file, data):
    try:
        f = open(file, 'w')
        f.write(json.dumps(data))
        f.close()
        return True
    except:
        print("Save failed.")
        return False

def save_primary(file,newconfig):
    print("Saving desired to primary config")
    return save_json(file,newconfig)

def backup_primary():
    dirlist = uos.listdir()
    if config.espMAC not in dirlist:
        print("No primary config to backup ...")
        return True
    print("Renaming current to alternate config")
    try:
        if config.espMAC + ".alt" in dirlist:
            uos.remove(config.espMAC+".alt")
        uos.rename(config.espMAC, config.espMAC+".alt")
        return True
    except:
        return False

def update():

    # Get node files from http server
    desired = getjson(config.espMAC)
    latest = getjson("latestversions")

    if desired is None or latest is None:
        config.set('update_result',201)
        config.reboot(graceful=True)

    failedfiles = []
    changed = False

    for file in desired:
        skip=False
        if file == "nodename":
            skip = True

        if desired[file] == "latest":
            if file in latest:
                desired[file] = latest[file]
            else:
                print("\nError: Latest not in list for: {} \n".format(file))
                failedfiles.append(desired[file] + file)
                skip = True

        #skip if config.current matches desired
        if file in config.current:
            if config.current[file] == desired[file]:
                skip = True

        if not skip:
            changed = True
            if not save_file(file,desired[file]):
                failedfiles.append(desired[file] + file)
                print("{} failed".format(file))
            else:
                print("{} updated".format(file))

    if len(failedfiles) > 0:
        config.set('update_failed',202)
        print("\nFile fetch error! Check failedfiles (error=3)")
        try:
            with open('failedfiles','w') as f:
                for file in failedfiles:
                    f.write(file + "\n")
                f.close()
        except:
            print("Error writing to failedfiles ...")

    # Files fetched = success
    if len(failedfiles) == 0 and changed:

        # only backup pri-->alt if running on primary
        if config.get('config') == 1:
            result = backup_primary()
            if not result:
                print("Unable to save primary to alternate! (error=2)")
                config.set('update_result',203)
        else:
            print("\nWill save to primary config only ...")
            result = True

        if result:
            if save_primary(config.espMAC,desired):
                print("\nUpdate success!!\n")
                config.set('update_result',config.get('update'))
                config.set('config')
                config.clear('reboots')
            else:
                print("Error saving primary config! (error=1)")
                config.set('update_result',204)

    else:
        print("No changes made ...")
        config.set('update_result',config.get('update'))
        
    print("Exiting update gracefully ...")
    config.reboot(graceful=True)
