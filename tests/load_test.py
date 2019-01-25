import os, time
import requests
import json
import random
from requests.auth import HTTPBasicAuth

url = "http://live-cmx.cisco.com/notification"
payload = """{
    "notifications": [
        {
            "ipAddress": [
                "10.10.20.189"
            ],
            "ssid": "test",
            "band": "IEEE_802_11_B",
            "entity": "WIRELESS_CLIENTS",
            "timestamp": 1510287019249,
            "apMacAddress": "00:2b:01:00:05:00",
            "moveDistanceInFt": 117.988205,
            "notificationType": "movement",
            "locationMapHierarchy": "DevNetCampus>DevNetBuilding>DevNetZone>Zone2",
            "floorRefId": null,
            "locationCoordinate": {
                "x": 224.28616,
                "z": 0,
                "unit": "FEET",
                "y": 15.581566
            },
            "confidenceFactor": 32,
            "deviceId": "44:85:00:84:49:14",
            "subscriptionName": "Distance",
            "lastSeen": "2017-11-10T04:10:19.249+0000",
            "username": "",
            "eventId": 88571779,
            "geoCoordinate": {
                "unit": "DEGREES",
                "latitude": 36.1257356466829,
                "longitude": -97.06620710536545
            },
            "associated": true,
            "floorId": 723413320329068590
        }
    ]
}"""

NUM_PROCESSES = 10

def rand_mac():
    return "%02x:%02x:%02x:%02x:%02x:%02x" % (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
        )

def chunkIt(seq, num):
    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg

    return out

def notification(process_macs):
    good = 0
    for mac in process_macs:
        payload_json['notifications'][0]['deviceId'] = mac
        payload_json['notifications'][0]['moveDistanceInFt'] = random.randint(100, 150) + random.random()
        payload_json['notifications'][0]['locationCoordinate']['x'] = random.randint(100, 150) + random.random()
        payload_json['notifications'][0]['locationCoordinate']['y'] = random.randint(100, 150) + random.random()
        payload_json['notifications'][0]['floorId'] = random.randint(10, 15)
        random.randint(100, 150) + random.random()
        r = requests.post(url, json=payload_json, auth=HTTPBasicAuth('cmx', 'ugBxWwaI1/gjkFaLqLs9dMGvZLGsgthOyJOFHlwhChez2pQJkm+V95DK7U7dYjcWS/cs3hm5wn4XSmLaE14r8WWVWHSAcYkUuvX'))
        if r.status_code == 200:
            good += 1
    print('Finished requests - ',good)
    return


payload_json = json.loads(payload)

children = []

# create list of random mac's
macs = []
samples = 10000
for x in range(samples):
    macs.append(rand_mac())


mac_list = chunkIt(macs, NUM_PROCESSES)

start_time = time.time()
for process in range(NUM_PROCESSES):
    pid = os.fork()
    if pid:
        children.append(pid)
    else:
        notification(mac_list[process])
        os._exit(0)

for i, child in enumerate(children):
    os.waitpid(child,0)
    print('Child finished ', child)

delta = time.time() - start_time
rate = samples/delta
print("Time taken ", time.time() - start_time)
print("Transactions per sec", rate)
print("Target 180/sec")

