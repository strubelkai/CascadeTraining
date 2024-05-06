import requests
import os
from datetime import datetime, time, date, timezone, timedelta
from dotenv import load_dotenv
load_dotenv()


# <td>{{ activity.Activity }}</td>
# <td>{{ activity.Date }}</td>
# <td>{{ activity.Description }}</td>
# <td>{{ activity['Distance (KM)'] }}</td>



def getPlans():
    n=0
    today = date.today()
    previousMonday = today + timedelta(days=-(today.weekday()))
    plans = [
        {'Date': str(previousMonday+timedelta(days=n)), 'Activity': 'Bike',  'Description': '45 min', 'Distance (KM)':''},
        {'Date': str(previousMonday+timedelta(days=n+1)), 'Activity': 'Run and WeightTraining',  'Description': 'Chest/Tris', 'Distance (KM)':'5k'},
        {'Date': str(previousMonday+timedelta(days=n+2)), 'Activity': 'Swim and WeightTraining',  'Description': 'Back/Bis', 'Distance (KM)':'5x200M 30\"'},
        {'Date': str(previousMonday+timedelta(days=n+3)), 'Activity': 'Bike',  'Description': '45 min', 'Distance (KM)':''},
        {'Date': str(previousMonday+timedelta(days=n+4)), 'Activity': 'Swim and WeightTraining',  'Description': 'Shoulders/Abs', 'Distance (KM)':'1x500M 2\' and 5x100M 20\"'},
        {'Date': str(previousMonday+timedelta(days=n+5)), 'Activity': 'Run',  'Description': 'Long Run', 'Distance (KM)':'10k'},
        {'Date': str(previousMonday+timedelta(days=n+6)), 'Activity': 'WeightTraining',  'Description': 'Legs', 'Distance (KM)':''},
    ]
    return plans


if __name__ == '__main__':
    getPlans()