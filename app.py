#!flask/bin/python
from flask import Flask
from werkzeug.contrib.fixers import ProxyFix
from urllib2 import Request, urlopen

# CONSTANTS 
BASE_URL = 'https://iot.peoplepowerco.com/cloud/json/'
APP_JSON_CONTENT_TYPE = 'application/json'
USERNAME = 'myhaven.hack@gmail.com'
PASSWORD = 'myhaven1'
API_KEY = 'MQ-5r7R3-ewEsM8x7Tc1ZXYFIjSkiaZiOAUVTlHANegLw-EaSAk3XTAlmtc-AAkJ'
LOCATION_ID = '797'
# 


app = Flask(__name__)


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
