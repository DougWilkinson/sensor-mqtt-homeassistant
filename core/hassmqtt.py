# hassmqtt.py
import sys
import time
import json
import secrets
from machine import reset,Pin
import machine
from umqtt.simple import MQTTClient
import config

def version():
	return "23"
	# 23: support for new sensors (Device config)

class HassMqtt:

	positives = {'YES','ON','TRUE','OPEN'}
	negatives = {'NO','OFF','FALSE','CLOSED'}

	def __init__(self, nodename, sensor):
	
		self.nodename = nodename
		try:
			self.topics = secrets.custom_topics
		except:
			self.topics = ()
		self.hasstopic = secrets.hasstopic
		self.sensor = sensor
		self.lastmqttretry = time.time()

		self.client = MQTTClient(self.nodename, secrets.mqttserver, user=secrets.mqttuser, password=secrets.mqttpass)
		self.client.set_callback(self.Callback)
		self.mqttreconnects = config.Device("mqttreconnects",'sensor', 0, units='connections')
		self.hour = config.Device("hour",'sensor',-1, local=True)
		self.minute = config.Device("minute",'sensor',-1, local=True)
		self.Connect()

	def blink(self, times=1, speed_ms=100):
		led = Pin(2,Pin.OUT)
		for i in range(times):
			led.off()
			time.sleep_ms(speed_ms)
			led.on()
			time.sleep_ms(speed_ms)

	def Callback(self, topic, msg):
		#print(topic, msg)
		try:
			if "heartbeat" in topic:
				j = json.loads(msg)
				self.hour.value = int(j['Hour'])
				self.minute.value = int(j['Minute'])
				self.minute.updatevalue = True
			if "reset" in msg:
				print("MQTT Reset")
				self.client.disconnect()
				time.sleep(5)
				reset()
				while True:
					pass
			for key in self.sensor.list:
				if '/' + key + '/' in topic:
					sensor = self.sensor.list[key]
					dvalue = msg
					if sensor.type is int:
						dvalue = int(msg)
					if sensor.type is float:
						dvalue = float(msg)
					if sensor.type is str:
						dvalue = msg.decode()
					if sensor.type is bool:
						if msg.upper().decode() in HassMqtt.positives:
							dvalue = True
						if msg.upper().decode() in HassMqtt.negatives:
							dvalue = False
					# Update publish and value
					sensor.set(dvalue)
					sensor.updatevalue = True
		except:
			print("Error handling received MQTT data:")
			print(topic, msg)

	def Connect(self, clear=False):
		self.lastmqttretry = time.time()
		try:
			self.client.connect(clean_session=True)
			self.connected = True
		except:
			print("MQTTConnect failed ...")
			self.connected = False

		if self.connected:
			self.mqttreconnects.set(self.mqttreconnects.value + 1)
			print("MQTT connect count: {}".format(self.mqttreconnects.value))
			# Build HASS auto-discover and subscribe for each device
			for sensor, object in self.sensor.list.items():
				if not object.local:

					node_topic = "/{}/{}/{}".format(object.device_class, 
											self.nodename, 
											sensor)
					
					if object.config:
						msg = { "name": self.nodename + "_" + sensor }
						msg['stat_t'] = "hass" + node_topic + "/state"
						msg['json_attr_t'] = "hass" + node_topic + "/attrs"

						if object.device_class == "switch":
							msg['cmd_t'] = "hass" + node_topic + "/set"
						
						if object.device_class == "light":
							topic = node_topic.split("_")[0]
							msg['retain'] = "true"
							msg['cmd_t'] = "hass" + node_topic + "/set"
							msg['stat_t'] = "hass" + node_topic + "/state"
							msg['bri_cmd_t'] = "hass" + topic + "_bri/set"
							msg['bri_stat_t'] = "hass" + topic + "_bri/state"
							msg['rgb_cmd_t'] = "hass" + topic + "_rgb/set"
							msg['rgb_stat_t'] = "hass" + topic + "_rgb/state"

						if object.units is not None:
							msg['unit_of_meas'] = object.units
						
						self.client.publish("homeassistant" + node_topic + "/config", json.dumps(msg), retain=True)
					self.client.subscribe("hass" + node_topic + "/set" )
			# Subscribe to custom topics
			for t in self.topics:
				try:
					self.client.subscribe(t)
				except:
					print('Error subscribing to custom topic: ',t)

			try:
				f = open('debug')
				msg = f.read()
				f.close()
			except:
				msg = "No debug output"
			self.client.publish("hass/" + self.nodename + "/debug", msg, retain=True)

	def Spin(self):
		if not self.sensor.config.wlan.isconnected():
			self.sensor.config.wlan.connect()
			self.blink()

		if self.connected:
			try:
				error_msg = "check_msg() failed ..."
				self.client.check_msg()
				error_msg = "Publish() failed ..."
				self.Publish()
			except KeyboardInterrupt:
				print("hassmqtt: Ctrl-C detected")
				raise
			except:
				print(error_msg)
				self.connected = False
		
		if not self.connected and time.time() - self.lastmqttretry > 10:
			print("Attempting to reconnect ...")
			self.Connect()
   
	def Publish(self):
		
		for sensor, object in self.sensor.list.items():
			if object.changed and not 'local' in object.attrs:
				base = "{}/{}/{}/{}".format("hass", 
											object.device_class, 
											self.nodename, 
											sensor)

				if object.type is bool:
					if object.value:
						pubval = "ON"
					else:
						pubval = "OFF"
				else:
					pubval = str(object.value)

				self.client.publish(base + "/state", pubval, retain=True)
				if object.attrs != {}:
					self.client.publish(base + "/attrs", json.dumps(object.attrs), retain=True)
				object.changed = False


