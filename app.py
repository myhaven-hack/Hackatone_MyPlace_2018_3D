#!flask/bin/python
from flask import Flask
from flask import request
from flask import jsonify
from werkzeug.contrib.fixers import ProxyFix
from urllib2 import Request, urlopen
import json

# CONSTANTS 
BASE_URL = 'https://iot.peoplepowerco.com/cloud/json/'
# APP_JSON_CONTENT_TYPE = 'application/json'
# USERNAME = 'myhaven.hack@gmail.com'
# PASSWORD = 'myhaven1'
API_KEY = 'MQ-5r7R3-ewEsM8x7Tc1ZXYFIjSkiaZiOAUVTlHANegLw-EaSAk3XTAlmtc-AAkJ'
DEVICE_IDS = ['f8f6a30c006f0d00', 'FFFFFFFF0069c64a', 'FFFFFFFF0069fdd0']
# 


app = Flask(__name__)


@app.route('/getdevicemeasurements')
def getDeviceMeasurements():
	headers = {
		'API_KEY': API_KEY
	}
	request.args.get('deviceId')
	req = Request(BASE_URL + 'devices/' + request.args.get('deviceId'), headers=headers)

	response_body = urlopen(req).read()

	json.dumps(json.loads(response_body)['device']['parameters'])
	response = {
		'id' : json.loads(response_body)['device']['id'],
		'locationId' : json.loads(response_body)['device']['locationId'],
		'parameters' : json.loads(response_body)['device']['parameters']
	}
	return json.dumps(response)


@app.route('/getdevices')
def getDevices():
	headers = {
		'API_KEY': API_KEY
	}
	request = Request(BASE_URL + 'devices?', headers=headers)

	response_body = urlopen(request).read()
	return response_body


@app.route('/')
def index():
	return "Hello, MyHaven!"


if __name__ == '__main__':
    app.run(debug=True)
