#__________________________________Copyright__________________________________#
'''
Copyright (c) 2013, Battelle Memorial Institute
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in
   the documentation and/or other materials provided with the
   distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation
are those of the authors and should not be interpreted as representing
official policies, either expressed or implied, of the FreeBSD
Project.

This material was prepared as an account of work sponsored by an
agency of the United States Government.  Neither the United States
Government nor the United States Department of Energy, nor Battelle,
nor any of their employees, nor any jurisdiction or organization that
has cooperated in the development of these materials, makes any
warranty, express or implied, or assumes any legal liability or
responsibility for the accuracy, completeness, or usefulness or any
information, apparatus, product, software, or process disclosed, or
represents that its use would not infringe privately owned rights.

Reference herein to any specific commercial product, process, or
service by trade name, trademark, manufacturer, or otherwise does not
necessarily constitute or imply its endorsement, recommendation, or
favoring by the United States Government or any agency thereof, or
Battelle Memorial Institute. The views and opinions of authors
expressed herein do not necessarily state or reflect those of the
United States Government or any agency thereof.

PACIFIC NORTHWEST NATIONAL LABORATORY
operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
under Contract DE-AC05-76RL01830
'''
#_____________________________________________________________________________#



#____________________________________About____________________________________#
'''
Brian Ruskauff
National Renewable Energy Labs (NREL)
10/9/15
Referenced from Kathleen Genger's agent.py code for dehumidifier control as well as ListenerAgent. References from Deepthi Vaidhynathan's communication code also included.


This code was made as a replacement for the controls implemented in a heat pump water heater (HPWH).

FUNCTIONALITY
-While the state of the HPWH is 0 it will not heat water or respond to control commands. Use the state as an emergency shuttoff.
-While the water temperature is higher than the low deadband limit the tank will not heat.
-If the upper or lower tank temperature drops below the low deadband limit but is above the low limit, the tank will heat with the heat pump until both temperatures are equal to the hi deadband limit. 
-If the tank temperature drops below the low limit, the tank will heat with the upper element until the upper tank temperature is equal to the hi deadband limit. It will then heat with the lower element until the lower tank temperature is equal to the hi deadband limit. While heating with the lower element, if the upper tank temperature drops below the hi deadband limit, the tank will heat with the upper element to reach the hi deadband limit once again, and then switch back to the lower element. Once both tank temperatures are equal to the hi deadband limit the tank will stop heating.

INPUT - Status Request Signals from Controlling Agent
	Request the state of the HPWH
		- topic = 'control/request/state'
		- message does not matter
	Request the mode of the HPWH
		- topic = 'control/request/mode'
		- message does not matter
	Request the Temperature Setpoint of the HPWH
		- topic = 'control/request/temp_desired'
		- message does not matter
	Request the Upper and Lower Tank Temperatures of the HPWH
		- topic = 'control/request/temp_tank'
		- message does not matter
	Request the deadband information of the HPWH
		- topic = 'control/request/deadbands'
		- message does not matter
**For info regarding the response of the HPWH, view the OUTPUT comments**

INPUT - Control Signals from Controlling Agent
	Control the State of the HPWH
		- topic = 'control/input/state'
		- message = [state]
	Control the Mode of the HPWH
		- topic = 'control/input/mode'
		- message = [mode]
	Control the Desired Temperature of the HPWH
		- topic = 'control/input/temp_desired'
		- message = [temp_desired]
	Control the Deadbands of the HPWH
		- topic - 'control/input/deadbands'
		- message = [dbl1, dbl2, dbl3]
**For specific message information, view the OUTPUT comments. Messages are the same**

OUTPUT - Status Signals from the HPWH
	Publish the state of the HPWH
		- topic = 'HPWH/state'
		- message = [state]
			- integer
			- state is 0 (off) or 1 (on)
			- while off HPWH will not respond to signals and will not power any
				heating elements
	Publish the mode of the HPWH
		- topic = 'HPWH/mode'
		- message = [mode]
			- string
			- state is "HP" (Heat Pump), "UE" (Upper Element),
				"LE" (Lower Element), or "SB" (standby)
	Publish the Temperature Setpoint of the HPWH
		- topic = 'HPWH/temp_desired'
		- message = temp_desired
			- double
			- Fahrenheit
			- can also be thought of as the set-point temperature
	Publish the Upper and Lower Tank Temperatures of the HPWH
		- topic = 'HPWH/temp_tank'
		- message = [temp_upper, temp_lower]
			- double
			- Fahrenheit
	Publish the deadband information of the HPWH
		- topic = 'HPWH/deadbands'
		- message does not matter
			- double
			- Fahrenheit
			- hi_deadband limit = temp_desired + dbl1
			- low_deadband limit = temp_desired + dbl2
			- low_limit = temp_desired + dbl3
'''
#_____________________________________________________________________________#



#____________________________________Setup____________________________________#

# Import Python dependencies
import logging, sys, time, settings, datetime

# Not sure I actually need this
from zmq.utils import jsonapi

# Import VOLTTRON dependencies
from volttron.platform.agent import BaseAgent, PublishMixin, periodic, utils, matching

# Import PyBBIO library for controlling BBB
from bbio import *

# Import Adafruit library for reading thermocouples
import Adafruit_BBIO
import Adafruit_MAX31855.MAX31855 as MAX31855

# Enable information and debug logging
utils.setup_logging()
_log = logging.getLogger(__name__)
#_____________________________________________________________________________#



#____________________________________Agent____________________________________#  

# Blink an LED based off of input from user and demand agents
class HPWHControlAgent(PublishMixin, BaseAgent):

	def __init__(self, config_path, **kwargs):
		super(HPWHControlAgent, self).__init__(**kwargs)

		# load library from config file
		self.config = utils.load_config(config_path)

		'''Set up GPIO pins for control_____________________________________'''
		# Make variables for GPIO pins controlling the HPWH
		self.fan1 = GPIO1_15	# fan 1 (P8_15)
		self.fan2 = GPIO1_14	# fan 2 (P8_16)
		self.fan1_pwm = PWM1A	# fan 2 speed (P9_14)
		self.fan2_pwm = PWM2B	# fan 2 speed (P8_13)
		self.HP = GPIO1_13	# heat pump relay (P8_11, RY1)
		self.up_element = GPIO1_12	# upper element (P8_12, RY2)
		self.low_element = GPIO0_26	# lower element (P8_14, RY3)
		# Initialize GPIO pin mode
		pinMode(self.fan1, OUTPUT)
		pinMode(self.fan2, OUTPUT)
		pinMode(self.HP, OUTPUT)
		pinMode(self.up_element, OUTPUT)
		pinMode(self.low_element, OUTPUT)
		# Initialize output pins to LOW (off)
		digitalWrite(self.fan1, LOW)
		digitalWrite(self.fan2, LOW)
		digitalWrite(self.HP, LOW)
		digitalWrite(self.up_element, LOW)
		digitalWrite(self.low_element, LOW)
		# Initialize fans to 0 duty cycle
		analogWrite(self.fan1_pwm, 0)
		analogWrite(self.fan2_pwm, 0)
		# Set PWM frequency to 15,000 Hz
		pwmFrequency(self.fan1_pwm, 15000)
		pwmFrequency(self.fan2_pwm, 15000)
		'''_________________________________________________________________'''


		'''Set up GPIO pins for measuring temperature_______________________'''
		# Make variables for ADC Pins
		self.ADC = AIN4
		# Set up pins for SPI interface, thermocouple readings
		CLK = 'P9_12'
		CS = 'P9_15'
		DO = 'P9_23'
		self.sensor_up = MAX31855.MAX31855(CLK, CS, DO)
		CLK = 'P8_7'
		CS = 'P8_8'
		DO = 'P8_9'
		self.sensor_low = MAX31855.MAX31855(CLK, CS, DO)
		'''_________________________________________________________________'''


		'''Variables for Control Logic______________________________________'''
		# Initialize flags
		self.state = 0
		self.fast = 0
		self.regular = 0
		self.mode = "HPWH is off. Turn on for water heating."
		self.cost_level = "low"
		self.cost = 0
		# Initialize upper & lower sensor temps (set to same as desired_temp)
		self.up_temp = 120
		self.low_temp = 120
		# Initialize default temp
		self.desired_temp = 120
		# Initialize variables for deadband
		self.dbl1, self.dbl2, self.dbl3 = 0, -18, -22
		# High deadband limit is 0F above desired temp
		self.hi_deadband = self.desired_temp + self.dbl1
		# Low deadband limit is 18F below desired temp
		self.low_deadband = self.desired_temp + self.dbl2
		# Lowest limit before elements turn on is 22F below desired temp
		self.low_limit = self.desired_temp + self.dbl3
		'''_________________________________________________________________'''


		'''Variables for Measurement Logic__________________________________'''
		# nn is a placeholder for list operations
		self.nn = 0
		# ii is total samples to keep in moving avg. time*samplerate
		self.ii = settings.seconds * 1 / settings.temp_int
		# Initialize empty values lists
		self.values_up = [0]*int(self.ii)
		self.values_low = [0]*int(self.ii)
		'''_________________________________________________________________'''


	# Additional Setup
	def setup(self):
		# Publish message from config file, usually a setup msg
		_log.info(self.config['message'])
		super(HPWHControlAgent, self).setup()


	'''Operational Modules__________________________________________________'''
	# Function to test for numbers
	def is_int(self, numb):
		try:
			int(numb)
			return True
		except ValueError:
			return False
	# Define Deadbands
	def deadbands(self, hi, low, loww):
		self.hi_deadband = self.desired_temp + hi
		self.low_deadband = self.desired_temp + low
		self.low_limit = self.desired_temp + loww
	# Turn everything off
	def all_OFF(self):
		# Make sure heating elements are off
		digitalWrite(self.up_element, LOW)
		digitalWrite(self.low_element, LOW)
		# Turn the HP off
		digitalWrite(self.HP, LOW)
		# Turn the fans off
		self.fans_OFF()
	# Turn on Fans
	def fans_ON(self):
		# Set duty cycle to 85% (8 bit has 256 steps)
		analogWrite(self.fan1_pwm, (255*85/100))
		analogWrite(self.fan2_pwm, (255*85/100))
		# Turn on Fans (opens MOSFETs)
		digitalWrite(self.fan1, HIGH)
		digitalWrite(self.fan2, HIGH)
	# Turn off Fans
	def fans_OFF(self):
		digitalWrite(self.fan1, LOW)
		digitalWrite(self.fan2, LOW)
	# Turn on HP
	def HP_ON(self):
		# Make sure heating elements are off
		digitalWrite(self.up_element, LOW)
		digitalWrite(self.low_element, LOW)
		# Turn the fans on
		self.fans_ON()
		# Turn the HP on
		digitalWrite(self.HP, HIGH)
	# Turn on Upper Element
	def UpElement_ON(self):
		# Make sure lower heating element, hp and fans are off
		digitalWrite(self.low_element, LOW)
		digitalWrite(self.HP, LOW)
		self.fans_OFF()
		# Turn the upper heating element on
		digitalWrite(self.up_element, HIGH)
	# Turn on Lower Element
	def LowElement_ON(self):
		# Make sure upper heating element, hp and fans are off
		digitalWrite(self.up_element, LOW)
		digitalWrite(self.HP, LOW)
		self.fans_OFF()
		# Turn the lower heating element on
		digitalWrite(self.low_element, HIGH)
	'''_____________________________________________________________________'''


	'''Handle Requests from Control Agent___________________________________'''
	# Request for State Information
	@matching.match_start('control/request/state')
	def give_state(self, topic, headers, message, match):
		self.publish_json('HPWH/state', {}, (self.state))
	# Request for Mode Information
	@matching.match_start('control/request/mode')
	def give_mode(self, topic, headers, message, match):
		self.publish_json('HPWH/mode', {}, (self.mode))
	# Request for Temperature SetPoint Information
	@matching.match_start('control/request/temp_desired')
	def give_temp_desired(self, topic, headers, message, match):
		self.publish_json('HPWH/temp_desired', {}, (self.temp_desired))
	# Request for Temperature Information
	@matching.match_start('control/request/temp_tank')
	def give_temp(self, topic, headers, message, match):
		self.publish_json('HPWH/temp_tank', {}, (self.up_temp, self.low_temp))
	# Request for Deadband Information
	@matching.match_start('control/request/deadbands')
	def give_deadbands(self, topic, headers, message, match):
		self.publish_json('HPWH/deadbands', {}, (self.hi_deadband,
				self.low_deadband, self.low_limit))
	'''_____________________________________________________________________'''


	'''Handle Inputs from Control Agent_____________________________________'''
	# Check for Control Input - State
	@matching.match_start('control/input/state')
	def define_state(self, topic, headers, message, match):
		# Control Agent publishes message = [state]
		state_info = jsonapi.loads(message[0])
		self.state = state_info[0]
	# Check for Control Input - Mode
	@matching.match_start('control/input/mode')
	def define_mode(self, topic, headers, message, match):
		# Control Agent publishes message = [mode]
		self.mode = jsonapi. loads(message[0])
	# Check for Control Input - Temperature
	@matching.match_start('control/input/temp_desired')
	def define_temp(self, topic, headers, message, match):
		# Control Agent publishes message = [desired_temp]
		temp_info = jsonapi.loads(message[0])
		self.desired_temp = temp_info[0]
		# Redefine Deadbands
		self.deadbands(self.dbl1, self.dbl2, self.dbl3)
	# Check for Control Input - Deadbands
	@matching.match_start('control/input/deadbands')
	def define_deadbands(self, topic, headers, message, match):
		# Control Agent publishes message = [dbl1, dbl2, dbl3]
		deadband_info = jsonapi. loads(message[0])
		(self.dbl1, self.dbl2, self.dbl3 = deadband_info[0], deadband_info[1],
				deadband_info[2])
		# Redefine Deadbands
		self.deadbands(self.dbl1, self,dbl2, self.dbl3)
	'''_____________________________________________________________________'''

	'''Periodically Update Tank Temperatures________________________________'''
	@periodic(settings.temp_int)
	# Measure tank temperature, perform moving average for stability
	def measure_temp(self):
		# Read temp and convert to Fahrenheit
		temp_up = self.sensor_up.readTempC() * 9 / 5 + 32
		temp_low = self.sensor_low.readTempC() * 9 / 5 + 32
		# Add newest reading if neither reading is nan
		if self.is_int(temp_up) and self.is_int(temp_low):
			# Add newest temp reading to list
			self.values_up[self.nn] = temp_up
			self.values_low[self.nn] = temp_low
			self.nn += 1
		# Find average in value lists, re-linearize for t-type from k-type
		self.temp_up = ((sum(self.values_up)/len(self.values_up)) /
				1.029 + 2.3295)
		self.temp_low = ((sum(self.values_low)/len(self.values_low)) /
				1.029 + 2.3295)
		# Reset nn when at end of list
		if self.nn == self.ii:
			self.nn = 0
	'''_____________________________________________________________________'''


	'''Periodically Update Operation Mode___________________________________'''
	@periodic(settings.mode_int)
	# Check temperature periodically and adjust controls accordingly
	def HPWH_Control(self):
		up_temp = self.up_temp
		low_temp = self.low_temp
		if self.state == 0:
			self.all_OFF()
			self.mode = "SB"
		elif self.state == 1:
			# Check if elements are above deadband
			if up_temp > self.desired_temp and low_temp > self.desired_temp:
				# Turn everything off and set to regular operation
				self.fast = 0
				self.regular = 0
				self.all_OFF()
				self.mode = "SB"
			# Check if either temp readings are below low_limit
			elif ((up_temp < self.low_limit or low_temp < self.low_limit) or
					(low_temp < self.desired_temp and self.fast == 1)):
				# Fast is a variable to signal quick heating is needed
				self.fast = 1
				self.regular = 0
				# If upper temp is too cold turn on the upper heating element
				if up_temp < self.hi_deadband:
					self.UpElement_ON()
					self.mode = "UE"
				# If only lower temp is too cold turn on lower heating element
				elif low_temp < self.hi_deadband:
					self.LowElement_ON()
					self.mode = "LE"
			# Check if both temp readings are in deadband
			elif (up_temp >= self.low_deadband and low_temp >= self.low_deadband
					and self.regular == 0):
				# Turn everything off and set to regular operation
				self.all_OFF()
				self.fast = 0
				self.regular = 0
				self.mode = "SB"
			# Check if either temp readings are below deadband but above
			# low_limit
			elif ((up_temp < self.low_deadband and up_temp >= self.low_limit) or
					(low_temp < self.low_deadband and low_temp >= 
					self.low_limit) or (self.regular == 1)):
				self.fast = 0
				self.regular = 1
				if low_temp >= self.hi_deadband:
					self.regular = 0
				# Turn HP on
				self.HP_ON()
				self.mode = "HP"
	'''_____________________________________________________________________'''
#_____________________________________________________________________________#



#________________________________Platform Stuff_______________________________#

# Enable Agent to parse arguments on the command line by the agent launcher
def main(argv=sys.argv):
    # Main method called by the platform.
    utils.default_main(HPWHControlAgent,
                       description='HPWH Control Agent',
                       argv=argv)

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
