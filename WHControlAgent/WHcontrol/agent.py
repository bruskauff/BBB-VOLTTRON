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
9/8/15
Referenced from Kathleen Genger's agent.py code for dehumidifier control as well as ListenerAgent


This code was made to modulate the blinking rate of an LED. At low energy costs it will blink the LED every 1/4 of a second. At medium energy rates it will blink the LED every 1 second. At high energy rates it will blink the LED every 5 seconds. The duration of the on cycle is fixed at 1/16 of a second. If it is receiving an invalid signal from the demand agent it will blink the LED every 0.02 seconds to appear to be always on (use for debugging).

This script can also allow direct user control of the LED flash interval. It will also let the user turn the flashing on or off.

INPUT 
	- signal from DemandAgent with [costlevel, cost]
		- costlevel is 'high', 'medium', or 'low'
		- cost is a float in dollars
	- signal from UserAgent with [state, interval]
		- state is 'ON' or 'OFF'
		- interval
OUTPUT
	- logs the inputted cost level, cost, and interval
'''
#_____________________________________________________________________________#



#____________________________________Setup____________________________________#

# Import Python dependencies
import logging, sys, time, settings

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
class WHControlAgent(PublishMixin, BaseAgent):

	def __init__(self, config_path, **kwargs):
		super(WHControlAgent, self).__init__(**kwargs)

		# load library from config file
		self.config = utils.load_config(config_path)

		# Make variables for GPIO Pins
		self.up_element = GPIO1_7	# upper element (P8_4, RY2)
		self.low_element = GPIO1_2	# lower element (P8_5, RY3)
		# Initialize GPIO pin mode
		pinMode(self.up_element, OUTPUT)
		pinMode(self.low_element, OUTPUT)
		# Initialize output pins to LOW (off)
		digitalWrite(self.up_element, LOW)
		digitalWrite(self.low_element, LOW)

	# Additional Setup
	def setup(self):
		# Publish message from config file, usually a setup msg
		_log.info(self.config['message'])
		super(WHControlAgent, self).setup()

	# Turn on Upper Element
	def UpElement_ON(self):
		# Make sure lower heating element is off
		digitalWrite(self.low_element, LOW)
		# Turn the upper heating element on
		digitalWrite(self.up_element, HIGH)

	# Turn off Upper Element
	def UpElement_OFF(self):
		# Make sure lower heating elementis off
		digitalWrite(self.low_element, LOW)
		# Turn the upper heating element off
		digitalWrite(self.up_element, LOW)

	# Turn on Lower Element
	def LowElement_ON(self):
		# Make sure upper heating element is off
		digitalWrite(self.up_element, LOW)
		# Turn the lower heating element on
		digitalWrite(self.low_element, HIGH)

	# Turn off Lower Element
	def LowElement_OFF(self):
		# Make sure upper heating element is off
		digitalWrite(self.up_element, LOW)
		# Turn the lower heating element off
		digitalWrite(self.low_element, LOW)

	# Check for User Input - Temperature
	@matching.match_start('user/temp')
	# Define the desired temperature
	def define_temp(self, topic, headers, message, match):
		# User Agent published message = [temp]
		temp_info = jsonapi.loads(message[0])
		self.desired_temp = temp_info[1]
		# High deadband limit is 5F above desired temp
		self.hi_deadband = self.desired_temp + 5
		# Low deadband limit is 5F below desired temp
		self.low_deadband = self.desired_temp - 5
		# Lowest limit before elements turn on is 20F below desired temp
		self.low_limit = self.desired_temp - 20

	# Check for User Input - Mode
	@matching.match_start('user/mode')
	# Define state of operation: HP, upper element, lower element, off, on(auto)
	def define_mode(self, topic, headers, message, match):
		# User Agent published message = [old_mode, new_mode]
		mode_info = jsonapi.loads(message[0])
		old_mode = state_info[0] # May be utilized in future iteration
		self.mode = state_info[1]
		# If sate is off, turn off LED
		if self.state == False:
			self.LED1_OFF()

	# Check for utility Agent Activity
	@matching.match_start('utility/power_cost')
	# Adjust temp settings based on power level
	def define_interval(self, topic, headers, message, match):
		# Utility Agent publishes message = [cost_level, cost]
		cost_info = jsonapi.loads(message[0])
		cost_level = cost_info[0]
		cost = cost_info[1]

		if cost_level == 'low':
			print "Keep deadband in current location"
		elif cost_level == 'medium':
			# Shift low_limit 5F lower
			self.low_limit = self.desired_temp - 25
		elif cost_level == 'high':
			# Shift low_limit and deadband 5F lower
			self.hi_deadband = self.desired_temp + 0
			self.low_deadband = self.desired_temp - 10
			self.low_limit = self.desired_temp - 25

		# Log information & action
		_log.info("Cost level is %s at $%s, setting deadband to %r - %r deg F."
				%(cost_level, cost, self.low_deadband, self.hi_deadband))

	# Use User Agent to simulate & test temp input
	@matching.match_start('user/temp_sim')
	def set_temp(self, topic, headers, message, match):
		# User agent publishes message = [up_temp, low_temp]
		temp_info = jsonapi.loads(message[0])
		self.up_temp = temp_info[0]
		self.low_temp = temp_info[1]

	# Check temperature periodically and adjust controls accordingly
	@periodic(settings.interval)
	# Adjust controls accroding to temperature
	def HPWH_Control(self):
		# Check if both temp readings are in deadband
		if up_temp >= self.low_deadband and low_temp >= self.low_deadband:
			# Turn everything off
			self.HP_OFF()
			self.UpElement_OFF()
			self.LowElement_OFF()
			# Fast is a conditional variable to signal quick heating is needed
			fast = False
		# Check if either temp readings are below low_limit
		elif ((up_temp < self.low_limit or low_temp < self.low_limit) or
				(low_temp < self.low_deadband and fast == True)):
			fast = True
			# If upper temp is too cold turn on the upper heating element
			if up_temp < self.low_deadband:
				self.UpElement_ON()
			# If only lower temp is too cold turn on lower heating element
			elif low_temp < self.low_deadband:
				self.LowElement_ON()
		# Check if either temp readings are below deadband but below low_limit
		elif ((up_temp < self.low_deadband and up_temp >= self.low_limit) or
				(low_temp < self.low_deadband and low_temp >= self.low_limit)):
			fast = False
			# Turn HP on
			self.HP_ON()
#_____________________________________________________________________________#



#___________________________________Closure___________________________________#

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
