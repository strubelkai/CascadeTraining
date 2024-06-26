import requests
import os
from datetime import datetime, time, date, timezone, timedelta
from dotenv import load_dotenv
load_dotenv()

global refresh_token

auth_url="https://www.strava.com/oauth/token"
activities_url = "https://www.strava.com/api/v3/athlete/activities?access_token="


def getRefreshToken(code):
    url = "https://www.strava.com/oauth/token"
    payload={
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'code': code,
        'grant_type': 'authorization_code',
        'f': 'json'
    }
    res = requests.post(url, data=payload, verify=False)
    global refresh_token
    refresh_token = res.json()['refresh_token']
    return refresh_token

def getStravaActivites(id):
    payload={
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'refresh_token': refresh_token, #os.getenv('REFRESH_TOKEN'),
        'grant_type': 'refresh_token',
        'f': 'json'
    }
    res = requests.post(auth_url, data=payload, verify=False)
    access_token = res.json()['access_token']

    header = {'Authorization': 'Bearer ' + access_token}
    param = {'id': id, 'includeAllEfforts': False}
    activities_url = "https://www.strava.com/api/v3/activities/"+str(id)+"?access_token="

    my_dataset = requests.get(activities_url, headers=header, params=param).json()

    return my_dataset

def getStravaData(days):
    payload={
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'refresh_token': refresh_token, #os.getenv('REFRESH_TOKEN'),
        'grant_type': 'refresh_token',
        'f': 'json'
    }
    res = requests.post(auth_url, data=payload, verify=False)
    access_token = res.json()['access_token']

    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 200, 'page': 1}
    my_dataset = requests.get(activities_url, headers=header, params=param).json()
    activity_list = []
    for d in my_dataset:
        date = datetime.fromisoformat(
            d['start_date'][:-1]
        )
        date_past = datetime.now() - timedelta(days=days)
        if (date > date_past):
            summary = {
                "Activity":str(d['sport_type']), 
                "Date":str(d['start_date']), #str(date.strftime("%m/%d, %H:%M"))
                "Time":str(round(d['elapsed_time']/60)),
                "Name":str(d['name']), 
                "id":str(d['id']), 
                "Distance (KM)":str(round(d['distance']/1000,2))
            }
            activity_list.append(summary)
    return list(reversed(activity_list))

if __name__ == '__main__':
    getStravaData()
