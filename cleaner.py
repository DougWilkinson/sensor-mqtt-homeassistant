# cleaner.py
import config
import uos,ujson

toclean = uos.listdir()

f = open('bcddc29e2a51.alt')
altfiles = ujson.load(f)
f.close()

tosave = ['bcddc29e2a51.alt','wifi.py','bcddc29e2a51','boot.py','failedfiles','bootloader.py','httpclient.py','ina219.py','re.py','webrepl_cfg.py','secrets.py']
for file,version in config.current.items():
    tosave.append(file+version+".py")
for file,version in altfiles.items():
    tosave.append(file+version+".py")

print("Files to save:",tosave)

for file in tosave:
    if file in toclean:
        toclean.pop(toclean.index(file))

print("files to be deleted:", toclean)

for file in toclean:
    uos.remove(file)