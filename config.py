#!/usr/local/bin/python3

DEBUG = False

# MQTT client
BROKER = "localhost"
PORT = 1883
TOPIC = "Telldus"
TOPIC_CLIMATE = "Climate"

# Telldus Local API
API = 'http://192.168.0.30/api/'
HEADERS = {
    'Authorization': 'Bearer xxxxxx'}

REQUEST_TIMEOUT = 10
REFRESH_TIMER = 10