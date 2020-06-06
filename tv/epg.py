import requests
from datetime import datetime
import xmltodict
import time
import sys
from concurrent.futures.thread import ThreadPoolExecutor

API = "http://jiotv.data.cdn.jio.com/apis/v1.3"
IMG = "http://jiotv.catchup.cdn.jio.com/dare_images"
channel = []
programme = []
error = []
result = []
done=0


def genEPG(i, c):
    global channel, programme, error, result, API, IMG, done
    for day in range(0, 2):
        try:
            resp = requests.get(f"{API}/getepg/get", params={"offset": day, "channel_id": c['channel_id'], "langId": "6"}).json()
            day == 0 and channel.append({
                "@id": c['channel_id'],
                "display-name": c['channel_name'],
                "icon": {
                    "@src": f"{IMG}/images/{c['logoUrl']}"
                }
            })
            for eachEGP in resp.get("epg"):
                pdict = {
                    "@start": datetime.utcfromtimestamp(int(eachEGP['startEpoch']*.001)).strftime('%Y%m%d%H%M%S'),
                    "@stop": datetime.utcfromtimestamp(int(eachEGP['endEpoch']*.001)).strftime('%Y%m%d%H%M%S'),
                    "@channel": eachEGP['channel_id'],
                    "title": eachEGP['showname'],
                    "desc": eachEGP['description'],
                    "category": eachEGP['showCategory'],
                    # "date": datetime.today().strftime('%Y%m%d'),
                    # "star-rating": {
                    #     "value": "10/10"
                    # },
                    "icon": {
                        "@src": f"{IMG}/shows/{eachEGP['episodePoster']}"
                    }
                }
                if eachEGP['episode_num'] > -1:
                    pdict["episode-num"] = {
                        "@system": "xmltv_ns",
                        "#text": f"0.{eachEGP['episode_num']}"
                    }
                if eachEGP.get("director") or eachEGP.get("starCast"):
                    pdict["credits"] = {
                        "director": eachEGP.get("director"),
                        "actor": eachEGP.get("starCast") and eachEGP.get("starCast").split(', ')
                    }
                if eachEGP.get("episode_desc"):
                    pdict["sub-title"] = eachEGP.get("episode_desc")
                programme.append(pdict)
        except Exception as e:
            print(e)
            error.append(c['channel_id'])
    done+=1
    # print(f"{done*100/len(result):.2f} %", end="\r")

if __name__ == "__main__":
    stime = time.time()
    prms = {"os": "android", "devicetype": "phone"}
    raw = requests.get(f"{API}/getMobileChannelList/get/", params=prms).json()
    result = raw.get("result")
    with ThreadPoolExecutor(max_workers=5) as e:
        e.map(genEPG, range(len(result)), result)
    epgdict = {"tv": {
        "channel": channel,
        "programme": programme
    }}
    epgxml = xmltodict.unparse(epgdict, pretty=True)
    with open(sys.argv[1], 'wb+') as f:
        f.write(epgxml.encode('utf-8'))
    print("EPG updated", datetime.now())
    if len(error) > 0:
        print(f'error in {error}')
    print(f"Took {time.time()-stime:.2f} seconds")