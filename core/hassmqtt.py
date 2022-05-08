# hassmqtt.py
import sys
from time import sleep_ms, time
import json
import secrets
from machine import soft_reset,Pin
import machine
from umqtt.simple import MQTTClient
from config import rtc, Device, wlan

def version():
	return "38" xx
	# 38: cleaned up some code to shrink size

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
		self.lastmqttretry = time()
		self.lastwifiretry = time()
		self.shutdown = False

		self.client = MQTTClient(self.nodename, secrets.mqttserver, user=secrets.mqttuser, password=secrets.mqttpass)
		self.client.set_callback(self.Callback)
		self.mqttreconnects = Device("mqttreconnects",'sensor', 0, units='connections')
		self.hour = Device("hour",'sensor',-1, local=True)
		self.minute = Device("minute",'sensor',-1, local=True)
		self.date = "00/00/00"
		self.Connect()

	def blink(self, times=1, speed_ms=100):
		led = Pin(2,Pin.OUT)
		for i in range(times):
			led.off()
			sleep_ms(speed_ms)
			led.on()
			sleep_ms(speed_ms)

	def Callback(self, topic, msg):
		#print(topic, msg)
		try:
			if "heartbeat" in topic:
				j = json.loads(msg)
				self.hour.value = int(j['Hour'])
				self.minute.value = int(j['Minute'])
				self.date = tuple(int(i) for i in tuple(j['Date'].split(',')))
				rtc.datetime(self.date)
				self.minute.updatevalue = True
			if "reset" in msg:
				print("Reset requested via MQTT")
				self.shutdown = True
				return
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

	def hasetup(self):
		if self.mqttconnected:
			# Build HASS auto-discover and subscribe for each device
			for sensor, object in self.sensor.list.items():
				if not object.local and not object.published:
					object.published = True
					node_topic = "/{}/{}/{}".format(object.device_class, 
													self.nodename, 
													sensor)
					
					if object.config:
						msg = { "name": self.nodename + "_" + sensor }
						msg['uniq_id'] = self.nodename + "_" + sensor
						msg['obj_id'] = self.nodename + "_" + sensor
						msg['stat_t'] = "hass" + node_topic + "/state"
						msg['json_attr_t'] = "hass" + node_topic + "/attrs"

						if object.device_class == "switch":
							msg['cmd_t'] = "hass" + node_topic + "/set"
							msg['retain'] = "true"
						
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
						
						try:
							self.client.publish("homeassistant" + node_topic + "/config", json.dumps(msg), retain=True)
						except:
							print("Failed to publish to: homeassistant/{}/config".format(node_topic))
					try:
						self.client.subscribe("hass" + node_topic + "/set" )
					except:
						print("Failed to subscribe to: hass/{}/set".format(node_topic))

	def Connect(self, clear=False):
		self.lastmqttretry = time()
		try:
			self.client.connect(clean_session=True)
			self.mqttconnected = True
		except:
			print("MQTTConnect failed ...")
			self.mqttconnected = False

		if self.mqttconnected:
			self.mqttreconnects.set(self.mqttreconnects.value + 1)
			print("MQTT connect count: {}".format(self.mqttreconnects.value))

			self.hasetup()

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
			self.blink()
			self.mqttconnected = False
			if time() - self.lastwifiretry > 15:
				print("Attempting to reconnect wifi ...")
				wlan.disconnect()
				wlan.active(False)
				wlan.active(True)
				wlan.connect()
				self.lastwifiretry = time()
		else:
			if not self.mqttconnected and time() - self.lastmqttretry > 10:
				print("Attempting to reconnect MQTT ...")
				self.Connect()
				self.lastmqttretry = time()

		for device in self.sensor.list.values():
			if device.poll == 0:
				continue
			if device.poll == -1 or (time() - device.lastpolled) > device.poll:
				device.poller()
				device.lastpolled = time()

		if self.mqttconnected:
			try:
				error_msg = "hasetup failed"
				self.hasetup()
				error_msg = "check_msg failed"
				self.client.check_msg()
				error_msg = "Publish failed"
				self.Publish()
			except KeyboardInterrupt:
				print("hassmqtt: Ctrl-C!")
				raise
			except:
				print(error_msg)
				self.mqttconnected = False
		if self.shutdown:
			print("Shutdown ...")
			try:
				self.client.disconnect()
			except:
				print("Error disconnecting client")
			print("Soft Reset!\n\n")
			soft_reset()
			while True:
				pass

	def Publish(self):
		
		for sensor, object in self.sensor.list.items():
			if object.changed and not object.local:
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


