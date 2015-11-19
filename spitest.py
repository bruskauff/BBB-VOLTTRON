import Adafruit_MAX31855.MAX31855 as MAX31855
import time, datetime

CLK = 'P9_12'
CS = 'P9_15'
DO = 'P9_23'
sensor = MAX31855.MAX31855(CLK, CS, DO)

mavg_time = 5	#seconds

print 'Press ^C to quit.\n'

def is_int(numb):
	print numb
	try:
		int(numb)
		return True
	except ValueError:
		return False

# ii is the number of values to keep based off of the sampling rate hertz
hertz = 5
#ii = mavg_time*hertz
ii = 300
nn = 0
values = [0]*ii
hertz = float(hertz)
while True:
	temp = sensor.readTempC() * 9 / 5 + 32
	internal = sensor.readInternalC() * 9 / 5 + 32
	values[nn] = temp
	nn += 1
	temp_avg = sum(values)/len(values)
	if nn == ii:
		nn = 0
		print 'Raw Temp: %s F' %temp
		print 'Thermocouple Avg Temp: %s F' %temp_avg
		print 'Internal Temp: %s F' %internal
	#time.sleep(1/hertz)
