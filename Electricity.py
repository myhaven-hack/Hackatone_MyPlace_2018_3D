
import urllib2
from datetime import datetime
import Authorization_File as af
import pandas as pd
import numpy as np
import matplotlib.pyplot as pp
import locale
import json
import traceback
import pathlib

locale.setlocale(locale.LC_ALL, "")


def query_api():
    headers = {
          'API_KEY': af.api['key']
            }
    device_id = af.api['Smart Plug']
    try:
        request = urllib2.Request("https://iot.peoplepowerco.com/cloud/json/devices/"+str(device_id)+"/parameters", headers=headers)
        query = json.loads(urllib2.urlopen(request).read())
        if query["resultCode"] == 0:
            # device on
            # retrieve current measurements
            devices = query["devices"]
            parameters = devices["parameters"]
            data = {"time received": devices["lastDataReceivedDate"], "status": parameters[-3]["outletStatus"],
                    "energy": parameters[0]["value"], "power": parameters[-2]["power"]}
            return [True, data]
        else:
            # Device not on
            return [False, ("Unsuccessful Query: "+str(query['resultCode']))]
    except urllib2.HTTPError as e:
        return [False, 'HTTPError = ' + str(e.code)]
    except urllib2.URLError as e:
        return [False, 'URLError = ' + str(e.reason)]
    except urllib2.HTTPException as e:
        return [False, 'HTTPException']
    except Exception:
        return [False, 'Generic Exception: ' + traceback.format_exc()]
    

def login():
    headers = {
          'Content-Type': 'application/json',
          'API_KEY': af.api['key']
            }
    try:
        request = urllib2.Request("https://iot.peoplepowerco.com/cloud/json/loginByKey", headers=headers)
        response = json.loads(urllib2.urlopen(request).read())
        if response['resultCode'] == 0:
            return [True, "We're In --- Commencing Script"]
        else:
            return [False, "Unsuccessful Login: "+str(response['resultCode'])]
    except urllib2.HTTPError as e:
        return [False, 'HTTPError = ' + str(e.code)]
    except urllib2.URLError as e:
        return [False, 'URLError = ' + str(e.reason)]
    except urllib2.HTTPException as e:
        return [False, 'HTTPException']
    except Exception:
        return [False, 'Generic Exception: ' + str(traceback.format_exc())]


def calculate_bill(total_kwh):
    if total_kwh > 1000:
        fuel_cost = (0.038570 * 1000) + (0.048570 * (total_kwh - 1000))
        non_fuel_cost = (0.046990 * 1000) + (0.056990 * (total_kwh - 1000))
    else:
        fuel_cost = (0.038570 * total_kwh)
        non_fuel_cost = (0.046990 * total_kwh)
    bill = locale.currency(fuel_cost + non_fuel_cost + 5.9, grouping=True)
    return bill


def calculate_remaining_hours(current_kwh, quota, avg_watt):
    remaining_kwh = current_kwh - quota
    hours = remaining_kwh / (avg_watt*1000)
    return hours


def generate_message(total_kwh, daily, weekly, monthly, avg_watt):
    today = str(datetime.now())
    bill = str(calculate_bill(total_kwh))
    remaining_hours_daily = str(calculate_remaining_hours(total_kwh, daily, avg_watt))
    remaining_hours_weekly = str(calculate_remaining_hours(total_kwh, weekly, avg_watt))
    remaining_hours_monthly = str(calculate_remaining_hours(total_kwh, monthly, avg_watt))
    message = ("As of {}, your current electricity bill is: ${}."
               "Please note that in: {} hours you will meet your daily threshold, "
               "{} hours you will meet your weekly threshold, and {} hours you will "
               "meet you monthly threshold").format(today, bill, remaining_hours_daily,
                                                    remaining_hours_weekly, remaining_hours_monthly)
    return message


def create_json_update(data):
    # if status code is 0, then we're good
    # otherwise, then device is not turned off
    # keep this simple binary decision.
    dic = {"Status Code": data['status'],
           "Information": {
               "Queried Time": data['time received'],
               "Current Power": data['power'],
               "Current Energy": data['energy'],
            }
           }
    return json.dumps(dic)


def create_graphs(type, quota, dataFrame, folder):
    title = "Time Series Graph - "+type+" Consumption"
    pp.title(title, size='x-large')
    pp.xlabel("DateTime", size='x-large')
    pp.ylabel("Bill Amount ($)", size='x-large')
    dataFrame[type].plot(figsize=(20, 10), subplots=False, marker="o", markersize=3, color='blue', alpha=0.5)
    pp.axhline(y=quota, color='red', linestyle='-', label="Threshold")
    pp.axhline(y=quota * 0.75, color='orange', linestyle='-', label="Close to Threshold")
    pp.axhline(y=quota * 0.5, color='yellow', linestyle='-', label="Half of Threshold")
    pp.axhline(y=quota * 0.25, color='green', linestyle='-', label="Half of Threshold")
    pp.tight_layout()
    tag = str(datetime.now())
    path = folder+'/'+tag+".png"
    pp.savefig(path, orientation='landscape')


if __name__ == "__main__":

    logged_in = login()
    if logged_in[0]:

        # Successful login
        print (logged_in[1])

        # Create folders in directory for graphs
        pathlib.Path("Daily Graphs").mkdir(parents=True, exist_ok=True)
        pathlib.Path("Weekly Graphs").mkdir(parents=True, exist_ok=True)
        pathlib.Path("Monthly Graphs").mkdir(parents=True, exist_ok=True)

        # set some standard threshold ($)
        daily_quota = 1
        weekly_quota = 5
        monthly_quota = 10

        # create data frame
        dataFrame = pd.DataFrame(columns=['time received', 'status', 'energy', 'power',
                                          'daily bill total', 'weekly bill total', 'monthly bill total'])
        dataFrame = dataFrame.set_index('time received')

        # initializing current amounts
        daily = 0
        weekly = 0
        monthly = 0

        # collect data and populate data frame
        collecting_data = query_api()
        while True:
            if collecting_data[0]:
                dataFrame = dataFrame.append(data=collecting_data[1], ignore_index=True)
                create_json_update(data)
                collecting_data = query_api()
            else:
                # Unable to Query
                print (collecting_data[1])
                break
    else:
        # Unsuccessful login
        print (logged_in[1])
    

    

