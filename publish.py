import json

def publish(mqttclient, basetopic, name, list):
    topublish = {}
    tosave = {}
    resetlist = []
    savechanged = False
    pubneeded = False
    for s in list:
        if s.pubneeded:
            pubneeded = True
            resetlist.append(s)
            #s.pubneeded = False
        for p in s.publish:
            topublish[p[0]] = p[1]
        if s.save:
            for p in s.publish:
                tosave[p[0]] = p[1]
        if s.save and s.pubneeded:
            savechanged = True
    if topublish != {} and pubneeded:
        #print(json.dumps(topublish))
        mqttclient.publish(basetopic+name, json.dumps(topublish))
    if tosave != {} and savechanged:
        #print(json.dumps(tosave))
        mqttclient.publish(basetopic+name+"/init", json.dumps(tosave), True)
    for s in resetlist:
        s.pubneeded = False
    

