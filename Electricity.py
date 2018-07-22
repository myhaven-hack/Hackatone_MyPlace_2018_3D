
import urllib2
import datetime
import Authorization_File as af
import pandas as pd
import numpy as np
import matplotlib.pyplot as pp
import locale
import json
import traceback
import pathlib2
from DataFrame import DF

locale.setlocale(locale.LC_ALL, "")


def query_api(deviceId, startDate, endDate):
	headers = {
			'API_KEY': af.api['key']
			}
	try: 
		url = ("https://iot.peoplepowerco.com/cloud/json/devices/"+deviceId+'/parametersByDate/'+startDate+'?endDate='+endDate)
		request = urllib2.Request(url, headers=headers)
		query = json.loads(urllib2.urlopen(request).read())
		if query["resultCode"] == 0:
			# Device on -- return query
			return [True, query]
		else:
			# Device not on -- return failure
			return [False, ("Unsuccessful Query: "+str(query['resultCode']))]
	except urllib2.HTTPError as e:
		return [False, 'HTTPError = ' + str(e.code)]
	except urllib2.URLError as e:
		return [False, 'URLError = ' + str(e.reason)]
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
	except Exception:
		return [False, 'Generic Exception: ' + str(traceback.format_exc())]


def calculate_bill(total_kwh):
	if total_kwh > 1000:
		# different calculation if kwh > 1,000
		fuel_cost = (0.038570 * 1000) + (0.048570 * (total_kwh - 1000))
		non_fuel_cost = (0.046990 * 1000) + (0.056990 * (total_kwh - 1000))
	else:
		fuel_cost = (0.038570 * total_kwh)
		non_fuel_cost = (0.046990 * total_kwh)
	money = fuel_cost + non_fuel_cost + 5.9
	bill = locale.currency(money, grouping=True)
	return [money,bill]


def generate_message(today, current_kwh_total, monthly_quota):
	[money, bill] = calculate_bill(current_kwh_total)
	quota = locale.currency(monthly_quota, grouping=True)
	if (monthly_quota < money):
		# Exceed
		exceed = locale.currency(money-monthly_quota, grouping=True)
		message = ("As of {}, your current bill is {}. Please note "
				"that you have exceeded your monthly quota of {} by {}.").format(today, bill, quota, exceed)
	else:
		savings = locale.currency(monthly_quota - money, grouping=True)
		message = ("As of {}, your current bill is {}. Please note "
				"that you are {} below you're monthly quota. Good Job!").format(today, bill, savings)
	return message


def convert_time(date_time):
	if "." in date_time:
		idx = date_time.index(".")+4
		final_date_time = datetime.datetime.strptime(date_time[:idx], "%Y-%m-%dT%H:%M:%S.%f")
		return str(datetime.datetime.strftime(final_date_time, "%Y-%m-%d %H:%M:%S.%f"))
	else:
		idx = 19
		final_date_time = datetime.datetime.strptime(date_time[:idx], "%Y-%m-%dT%H:%M:%S")
		return str(datetime.datetime.strftime(final_date_time, "%Y-%m-%d %H:%M:%S.000000"))


def api_time(date_time):
	date_time = datetime.datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S.%f")
	return str(datetime.datetime.strftime(date_time, "%Y-%m-%dT%H:%M:%S."))+"000-04:00"


def clean_data(data):
	clean_data = {"time received": [], "energy": [], "current_kwh_total": [], "current_bill": []}
	curr_total = 0
	for i in data['readings']:
		par =  i['params']
		for d in par:
			if d['name']=='energy':
				clean_data["time received"].append(convert_time(i['timeStamp']))
				val = eval(d['value'])/1000.0
				curr_total += val
				clean_data["energy"].append(val)
				clean_data["current_kwh_total"].append(curr_total)
				[money, bill] = calculate_bill(curr_total)
				clean_data["current_bill"].append(money)
	return clean_data


def create_graph(col, quota, dataFrame):
	title = "Time Series Graph - "+col+" Consumption"
	pp.title(title, size='x-large')
	pp.xlabel("DateTime", size='x-large')
	pp.ylabel("Bill Amount ($)", size='x-large')
	dataFrame[col].plot(figsize=(20, 10), subplots=False, marker="o", markersize=3, color='blue', alpha=0.5)
	# add horizontal lines to show thresholds
	pp.axhline(y=quota, color='red', linestyle='-', label="Threshold")
	pp.axhline(y=quota * 0.75, color='orange', linestyle='-', label="Close to Threshold")
	pp.axhline(y=quota * 0.5, color='yellow', linestyle='-', label="Half of Threshold")
	pp.axhline(y=quota * 0.25, color='green', linestyle='-', label="Half of Threshold")
	pp.grid(True)
	pp.tight_layout()
	pp.legend()
	path = "Graphs/"+col + ".png"
	pp.savefig(path, orientation='landscape')


def create_json_update(lastest_data, monthly_quota):
	# if status code is 0, then we're good
	# otherwise, then device is not turned off
	# keep this simple binary decision.
	total_kwh = float(lastest_data['current_kwh_total'])
	[money, bill] = calculate_bill(total_kwh)
	dic = {
			"Queried Time": str(lastest_data.index.values[0]),
			"Current Energy": float(lastest_data['energy']),
			"Current KWH Total": total_kwh,
			"Current Bill": bill
			}
	if (monthly_quota > money):
		dic["Current Savings"] = locale.currency(monthly_quota-money, grouping=True)
	else:
		dic["Current Exceed"] = locale.currency(money-monthly_quota, grouping=True)
	return json.dumps(dic)


def exceeded_monthly(current_kwh_total, monthly_quota):
	[money, bill] = calculate_bill(current_kwh_total)
	return (monthly_quota < money)


'''--------------------------------------------------------------------'''


if __name__ == "__main__":

	deviceId = af.device_ids["Smart Plug"]
	today = datetime.datetime.now()
	month_before = today + datetime.timedelta(days=-30)

	logged_in = login()

	print ("Passed Login")

	monthly_quota = 10.0

	if logged_in[0]:

		# Successful login
		print (logged_in[1])

		# Create folder for graphs
		pathlib2.Path("Graphs").mkdir(parents=True, exist_ok=True)

		print ("Passed Created Folder")

		# Collect data to populate df
		collecting_data = query_api(deviceId, api_time(str(month_before)), api_time(str(today)))

		print ("Passed Collected Data")

		if collecting_data[0]:
			# If we're able to collect data, do the following...

			# Clean Data
			cleaned_data = clean_data(collecting_data[1])

			print ("Passed Cleaned Data")

			# Create DataFrame
			dataFrame = DF(cleaned_data)

			print ("Passed Created DataFrame")

			# Get Recent/Lastest Update and AVG energy
			lastest_data = dataFrame.tail(1)
			current_kwh_total = float(lastest_data['current_kwh_total'])
			avg_energy = float(dataFrame['energy'].mean())

			print ("Passed Collected Info")

			# Check if Quota is met
			if exceeded_monthly(current_kwh_total, monthly_quota):

				print (generate_message(str(today), current_kwh_total, monthly_quota))

			# Create JSON object to send to WebAPP
			create_json_update(lastest_data, monthly_quota)

			print ("Passed JSON")

			dataFrame.to_string()

			print ("Passed DataFrame Print")

			create_graph('current_bill', monthly_quota, dataFrame)

			print ("Passed Create Graph")

		else:
			# If we're unable to collect data, do the following...

			# Print Error Message
			print (collecting_data[1])

			# Restart df
			dataFrame = dataFrame.restart()
	else:

		# Unsuccessful login
		print (logged_in[1])
