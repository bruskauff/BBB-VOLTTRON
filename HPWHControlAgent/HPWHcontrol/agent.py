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
Referenced from Kathleen Genger's agent.py code for dehumidifier control as well as ListenerAgent


This code was made as a replacement for the controls implemented in a heat pump water heater (HPWH). 

INPUT 
	- signal from UtilityAgent with [costlevel, cost]
		- costlevel is 'high', 'medium', or 'low'
		- cost is a float in dollars
	- signals from HPWHUserAgent with:
		- topic = 'user/temp'
		- message = [old_temp, new_temp]
		- topic = 'user/state'
		- message = [old_state, new_state]
		- topic = 'user/sim_temp'
		- message = [up_temp, low_temp]
	- signals from HPWHMeasureAgent with:
		- topic = 'measure/temp'
		- message = [up_temp, low_temp]
OUTPUT
	- when outputting status
		- topic = 'control/status'
		- message = [state, mode, desired_temp]
	- logs the inputted cost level, cost, and heating response.
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

		# Make variables for GPIO Pins
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

		# Initialize flags
		self.state = False
		self.fast = False
		self.regular = False
		self.mode = "off"
		self.cost_level = "low"
		self.cost = 0

		# Initialize upper & lower sensor temps (set to same as desired_temp)
		self.up_temp = 120
		self.low_temp = 120

		# Initialize default temp
		self.desired_temp = 120
		# High deadband limit is 0F above desired temp
		self.hi_deadband = self.desired_temp + 0
		# Low deadband limit is 18F below desired temp
		self.low_deadband = self.desired_temp - 18
		# Lowest limit before elements turn on is 22F below desired temp
		self.low_limit = self.desired_temp - 22

	# Additional Setup
	def setup(self):
		# Publish message from config file, usually a setup msg
		_log.info(self.config['message'])
		super(HPWHControlAgent, self).setup()

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

	# Log information and reaction
	def logger_guy(self, reaction):
		_log.info("Cost level: %s at $%s, Desired Temp: %sF, Deadband: %sF to "
				"%sF, Low Limit: %sF. H&L Temp: %sF & %sF %s" %
				(self.cost_level, self.cost, self.desired_temp, 
				self.low_deadband, self.hi_deadband, self.low_limit,
				self.up_temp, self.low_temp, reaction))

	# Define Deadbands
	def deadbands(self, hi, low, loww):
		self.hi_deadband = self.desired_temp + hi
		self.low_deadband = self.desired_temp + low
		self.low_limit = self.desired_temp + loww

	# Check for User Input - Temperature
	@matching.match_start('user/temp')
	# Define the desired temperature
	def define_temp(self, topic, headers, message, match):
		# User Agent published message = [old_temp, new_temp]
		temp_info = jsonapi.loads(message[0])
		self.desired_temp = temp_info[1]
		# Define Deadbands
		self.deadbands(0, -18, -22)
		# High deadband limit is 0F above desired temp
		# Low deadband limit is 18F below desired temp
		# Lowest limit before elements turn on is 22F below desired temp

	# Check for User Input - state
	@matching.match_start('user/state')
	# Define state of operation: On (True) or Off (False)
	def define_mode(self, topic, headers, message, match):
		# User Agent published message = [old_state, new_state]
		state_info = jsonapi.loads(message[0])
		old_state = state_info[0] # May be utilized in future iteration
		self.state = state_info[1]

	# Use User Agent to simulate & test temp input
	@matching.match_start('user/sim_temp')
	def set_temp(self, topic, headers, message, match):
		# User agent publishes message = [up_temp, low_temp]
		temp_info = jsonapi.loads(message[0])
		self.up_temp = temp_info[0]
		self.low_temp = temp_info[1]

	# Check for Measurement Input - Temperature
	@matching.match_start('measure/temp')
	# Define Upper and Lower tank temperatures
	def define_temp(self, topic, headers, message, match):
		# Instrument agent publishes message = [up_temp, low_temp]
		temp_info = jsonapi.loads(message[0])
		self.up_temp = temp_info[0]
		self.low_temp = temp_info[1]

	# Check for utility Agent Activity
	@matching.match_start('utility/cost_info')
	# Adjust temp settings based on power level
	def import_costs(self, topic, headers, message, match):
		# Utility Agent publishes message = [cost_level, cost]
		cost_info = jsonapi.loads(message[0])
		self.cost_level = cost_info[0]
		self.cost = cost_info[1]

		if self.cost_level == 'low':
			self.deadbands(0, -18, -22)
			print "Keep deadband in current location"
		elif self.cost_level == 'medium':
			# Shift low_limit 5F lower
			self.deadbands(0, -18, -27)
		elif self.cost_level == 'high':
			# Shift low_limit 5F lower and deadband 10F lower
			# and desired temp 5F lower
			self.deadbands(-5, -23, -27)

		# Log information & action
		_log.info("Cost level is %s at $%s, setting deadband to %r - %r deg F."
				%(self.cost_level, self.cost, self.low_deadband,
						self.hi_deadband))

	@periodic(settings.pub_int)
	# Publish the current mode of operation and tank temperature
	def send_status(self):
		self.publish_json('control/status', {}, (self.state, self.mode, 
				self.desired_temp))

	@periodic(settings.mode_int)
	# Check temperature periodically and adjust controls accordingly
	def HPWH_Control(self):
		up_temp = self.up_temp
		low_temp = self.low_temp
		if self.state == False:
			self.all_OFF()
			reaction = "HPWH is off. Turn on for water heating."
			self.logger_guy(reaction)
			self.mode = reaction
		elif self.state == True:
			# Check if elements are above deadband
			if up_temp > self.desired_temp and low_temp > self.desired_temp:
				# Turn everything off and set to regular operation
				self.fast = False
				self.regular = False
				self.all_OFF()
				reaction = ("Temperature acceptable. All off")
				self.logger_guy(reaction)
				self.mode = reaction
			# Check if either temp readings are below low_limit
			elif ((up_temp < self.low_limit or low_temp < self.low_limit) or
					(low_temp < self.desired_temp and self.fast == True)):
				# Fast is a variable to signal quick heating is needed
				self.fast = True
				self.regular = False
				# If upper temp is too cold turn on the upper heating element
				if up_temp < self.hi_deadband:
					self.UpElement_ON()
					reaction = ("Temperature is really low."
							" Heating w/ upper element.")
					self.logger_guy(reaction)
					self.mode = reaction
				# If only lower temp is too cold turn on lower heating element
				elif low_temp < self.hi_deadband:
					self.LowElement_ON()
					reaction = ("Temperature is really low."
							" Heating w/ lower element.")
					self.logger_guy(reaction)
					self.mode = reaction
			# Check if both temp readings are in deadband
			elif (up_temp >= self.low_deadband and low_temp >= self.low_deadband
					and self.regular == False):
				# Turn everything off
				self.all_OFF()
				self.fast = False
				self.regular = False
				# Log information and reaction
				reaction = "Temperature acceptable. All off."
				self.logger_guy(reaction)
				self.mode = reaction
			# Check if either temp readings are below deadband but above
			# low_limit
			elif ((up_temp < self.low_deadband and up_temp >= self.low_limit) or
					(low_temp < self.low_deadband and low_temp >= 
					self.low_limit) or (self.regular == True)):
				self.fast = False
				self.regular = True
				if low_temp >= self.hi_deadband:
					self.regular = False
				# Turn HP on
				self.HP_ON()
				reaction = "Temperature is low. Heating w/ heat pump."
				self.logger_guy(reaction)
				self.mode = reaction
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
