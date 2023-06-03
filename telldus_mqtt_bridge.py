#!/usr/bin/python3
import requests
import time
import datetime
import paho.mqtt.client as paho
import json

import config


def telldus_request(command, headers):
    command_request = config.API + command
    try:
        json_data = requests.request("GET", command_request, headers=headers, data='', timeout=config.REQUEST_TIMEOUT)

        dict_data = json_data.json()
        dict_data['success'] = True
        dict_data['message'] = 'OK'

    except requests.exceptions.ConnectionError:
        dict_data = {
            'success': False,
            'message': 'Connection Error'
        }
    except requests.exceptions.Timeout:
        dict_data = {
            'success': False,
            'message': 'Request timed out'
        }
    # except requests.exceptions:
    except:
        dict_data = {
            'error': True,
            'message': 'Unknown error'
        }

    return dict_data


def main():
    # MQTT populate list of devices and sensors
    try:
        device_list = telldus_request('devices/list', config.HEADERS)
        client1.publish(config.TOPIC + "/Devices", json.dumps(device_list['device']))

        sensor_list = telldus_request('sensors/list', config.HEADERS)
        client1.publish(config.TOPIC + "/Sensors", json.dumps(sensor_list['sensor']))

    except Exception as e:
        sensor_list = {}
        print(e)

    printbuffer = ''
    printbuffer_wind = ''
    printbuffer_rain = ''

    if config.DEBUG:
        print(str('*** {} ***').format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        print(str('Data source: {}').format(config.API))

    if 'success' not in sensor_list or not sensor_list['success']:
        print('Response contained no success.')
        time.sleep(config.REFRESH_TIMER)
        return

    if 'sensor' not in sensor_list:
        print('No sensors in response. API key wrong? Message: ' + sensor_list['message'])
        time.sleep(config.REFRESH_TIMER)
        return

    for sensor in sensor_list['sensor']:
        try:
            request = 'sensor/info?id=' + str(sensor['id'])
            sensor_read = telldus_request(request, config.HEADERS)

        except Exception as e:
            print(str('*** {} ***').format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            print(str(e))
            time.sleep(config.REFRESH_TIMER)
            return

        if sensor['model'] == 'temperaturehumidity' or sensor['model'] == 'F824':

            if config.DEBUG:
                printbuffer += str('{:15} {:>5}{}C').format(sensor['name'], sensor_read['data'][0]['value'], chr(176))
                printbuffer += str('{:>7}%\n').format(int(sensor_read['data'][1]['value']))

            # MQTT
            mqtt_humidity_data = {
		'measurement': 'humidity',
                'name': sensor['name'],
                'value': sensor_read['data'][1]['value'],
                'id': sensor['sensorId'],
                'model': sensor['model'],
                'lastUpdated': sensor_read['lastUpdated'],
                'source': 'Telldus'
            }
            client1.publish(config.TOPIC_CLIMATE + "/Humidity/" + sensor['name'], json.dumps(mqtt_humidity_data))

            # MQTT
            mqtt_temp_data = {
		'measurement': 'temperature',
                'name': sensor['name'],
                'value': sensor_read['data'][0]['value'],
                'id': sensor['sensorId'],
                'model': sensor['model'],
                'lastUpdated': sensor_read['lastUpdated'],
                'source': 'Telldus'
            }
            client1.publish(config.TOPIC_CLIMATE + "/Temperature/" + sensor['name'], json.dumps(mqtt_temp_data))

        elif sensor['model'] == '2914':  # rain sensor

            rain = {}
            i = 0
            while i < len(sensor_read['data']):
                rain[sensor_read['data'][i]['name']] = sensor_read['data'][i]['value']
                i += 1

            if config.DEBUG:
                printbuffer_rain += str('\nRegn totalt {:9} mm\n').format(rain['rtot'])
                printbuffer_rain += str('Regnintensitet {:>6} mm/h\n').format(rain['rrate'])
                printbuffer_rain += str('Väderstation batt {:>3}\n').format(sensor_read['battery'])

            # MQTT
            mqtt_rain_data = {
		'measurement': 'rain',
                'name': sensor['name'],
                'rtot': rain['rtot'],
                'rrate': rain['rrate'],
                'battery': sensor['battery'],
                'id': sensor['sensorId'],
                'model': sensor['model'],
                'lastUpdated': sensor_read['lastUpdated'],
                'source': 'Telldus'
            }
            client1.publish(config.TOPIC_CLIMATE + "/Rain/" + sensor['name'], json.dumps(mqtt_rain_data))

        elif sensor['model'] == '1984':  # wind sensor
            wind = {}
            i = 0
            while i < len(sensor_read['data']):
                wind[sensor_read['data'][i]['name']] = sensor_read['data'][i]['value']
                i += 1

            if config.DEBUG:
                printbuffer_wind += str('\nVindriktning {:>8}{}\n').format(wind['wdir'], chr(176))
                printbuffer_wind += str('Medelvind {:>11} m/s\n').format(wind['wavg'])
                printbuffer_wind += str('Byvind {:>14} m/s\n').format(wind['wgust'])

            # MQTT
            mqtt_wind_data = {
		'measurement': 'wind',
                'name': sensor['name'],
                'wdir': wind['wdir'],
                'wavg': wind['wavg'],
                'wgust': wind['wgust'],
                'id': sensor['sensorId'],
                'model': sensor['model'],
                'lastUpdated': sensor_read['lastUpdated'],
                'source': 'Telldus'
            }
            client1.publish(config.TOPIC_CLIMATE + "/Wind/" + sensor['name'], json.dumps(mqtt_wind_data))

        else:
            print('Unknown sensor type: ' + sensor['model'])

    if config.DEBUG:
        printbuffer += printbuffer_wind + printbuffer_rain
        print(printbuffer)

    time.sleep(config.REFRESH_TIMER)


if __name__ == "__main__":
    print("Telldus MQTT Bridge source " + config.API)

    client1 = paho.Client("Telldus_MQTT_bridge")  # create client object
    client1.connect(config.BROKER, config.PORT)  # establish connection

    # Loop da loop, forever and ever
    while True:
        main()
