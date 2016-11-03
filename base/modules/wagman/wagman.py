#!/usr/bin/python3

import zmq
import time

class wagmanListener(object):
	'''
	A thread to listen Wagman status from the ZMQ publisher
	Available information from this class will be...
	nc_heartbeat: last heartbeat time from nc
	nc_curr: int_current and last_updated
	nc_temp: int_tempterature and last_updated
	nc_fails: number of fails on booting
	nc_enabled: enable flag
	nc_media: media used on current booting

	gn_heartbeat: last heartbeat time from gn
	gn_curr: int_current and last_updated
	gn_temp: int_tempterature and last_updated
	gn_fails: number of fails on booting
	gn_enabled: enable flag
	gn_media: media used on current booting

	cs_heartbeat: last heartbeat time from conresense board

	wagman_id: identification of Wagman
	wagman_date: RTC of Wagman and last_updated
	wagman_curr: int_current and last_updated
	wagman_temp: temperature of Wagman
	wagman_humid: humidity of Wagman

	error: when no connection available to Wagman

	* some of the entities have 'ENTITY_lastupdated', telling the time when updated
	'''

	def __init__(self, status):
		self.socket = None
		self.isConnected = False
		self.isClosed = False

		self.status = status
		self.warn_shutdown = True
		self.connect()

	def close(self):
		self.isClosed = True
		if self.isConnected:
			self.disconnect()

	def connect(self):
		try: 
			context = zmq.Context()
			self.socket = context.socket(zmq.SUB)
			self.socket.setsockopt(zmq.RCVTIMEO, 5000)
			self.socket.setsockopt(zmq.SUBSCRIBE, b'')
			self.socket.connect ('ipc:///tmp/zeromq_wagman-pub')
			self.isConnected = True
		except (zmq.ZMQError, Exception) as e:
			pass

	def disconnect(self):
		if self.socket != None and self.isConnected:
			self.socket.close()
			self.isConnected = False

	def ssplit(self, str, separator = ' '):
		ret = []
		try:
			splits = str.split(separator)
			for item in splits:
				ret.append(item)
		except:
			pass
		return ret

	def get(self, key):
		if key in self.status:
			value = self.status[key]
			key_updated = key + "_lastupdated"
			if key_updated in self.status:
				last_updated = self.status[key_updated]
				return value, last_updated
			return value, None
		return None, None

	def run(self):
		while not self.isClosed:
			msg = ""
			try:
				msg = self.socket.recv_string()
			except (zmq.ZMQError, Exception) as e:
				self.disconnect()
				time.sleep(3)
				self.connect()

			if not msg:
				continue

			prefix, _, content = msg.partition(':')
			if "error" in prefix:
				self.status["error"] = content
				self.status["error_lastupdated"] = time.time()
				continue
			else:
				if "error" in self.status:
					del self.status["error"]
					if "error_lastupdated" in self.status:
						del self.status["error_lastupdated"]
			prefix, _, content = (content.strip()).partition(' ')

			if "nc" in prefix:
				if "heartbeat" in content:
					self.status['nc_heartbeat'] = time.time()
				elif "stopping" in content:
					# When Wagman tries to shut down nc
					# First, warn system
					# second, shutdown immediately
					if self.warn_shutdown:
						shutdown(warning=True)
						self.warn_shutdown = False
					else:
						shutdown(warning=False)
			elif "gn" in prefix:
				if "heartbeat" in content:
					self.status['gn_heartbeat'] = time.time()
			elif "cs" in prefix:
				if "heartbeat" in content:
					self.status['cs_heartbeat'] = time.time()
			elif "id" in prefix:
				self.status['wagman_id'] = content
			elif "date" in prefix:
				self.status['wagman_date'] = content
				self.status['wagmans_date_lastupdated'] = time.time()
			elif "cu" in prefix:
				splits = self.ssplit(content)
				if len(splits) < 4:
					pass
				else:
					self.status['wagman_curr'] = splits[0]
					self.status['wagman_curr_lastupdated'] = time.time()
					self.status['nc_curr'] = splits[1]
					self.status['nc_curr_lastupdated'] = time.time()
					self.status['gn_curr'] = splits[2]
					self.status['gn_curr_lastupdated'] = time.time()
					self.status['cs_curr'] = splits[3]
					self.status['cs_curr_lastupdated'] = time.time()
			elif "th" in prefix:
				splits = self.ssplit(content)
				if len(splits) < 3:
					pass
				else:
					self.status['nc_temp'] = splits[0]
					self.status['nc_temp_lastupdated'] = time.time()
					self.status['gn_temp'] = splits[1]
					self.status['gn_temp_lastupdated'] = time.time()
					self.status['cs_temp'] = splits[2]
					self.status['cs_temp_lastupdated'] = time.time()
			elif "env" in prefix:
				splits = self.ssplit(content)
				if len(splits) < 2:
					pass
				else:
					self.status['wagman_temp'] = splits[0]
					self.status['wagman_temp_lastupdated'] = time.time()
					self.status['wagman_humid'] = splits[1]
					self.status['wagman_humid_lastupdated'] = time.time()
			elif "fails" in prefix:
				splits = self.ssplit(content)
				if len(splits) < 2:
					pass
				else:
					self.status['nc_fails'] = splits[0]
					self.status['gn_fails'] = splits[1]
			elif "enabled" in prefix:
				splits = self.ssplit(content)
				if len(splits) < 3:
					pass
				else:
					self.status['nc_enabled'] = splits[0]
					self.status['gn_enabled'] = splits[1]
					self.status['cs_enabled'] = splits[2]
			elif "media" in prefix:
				splits = self.ssplit(content)
				if len(splits) < 2:
					pass
				else:
					self.status['nc_media'] = splits[0]
					self.status['gn_media'] = splits[1]
		self.disconnect()

class start(object):
	def __init__(self, status):
		wagman_status = wagmanListener(status)
		wagman_status.run()