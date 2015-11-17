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
11/5/15
Referenced from Kathleen Genger's code for dehumidifier control


This script regulates water draws for testing the heat pump water heater (HPWH)

INPUT 
	- signal from UserAgent with:
		- topic = 'user/waterdraw'
		- message = [state]
OUTPUT
	- outputs an I/O signal through a BeagbeBone Black's GPIO pin
	- when outputting status
		- topic = 'waterdraw/state'
		- message = [state]
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
class HPWHWaterDrawAgent(PublishMixin, BaseAgent):

	def __init__(self, config_path, **kwargs):
		super(HPWHWaterDrawAgent, self).__init__(**kwargs)

		# load library from config file
		self.config = utils.load_config(config_path)

		# Make variables for GPIO Pin
		self.draw = GPIO0_27	# (P8_17)
		# Initialize GPIO pin mode
		pinMode(self.draw, OUTPUT)
		# Initialize output pins to LOW (off)
		digitalWrite(self.draw, LOW)

		# Initialize state to off
		self.state = 0
		# Initialize water draw step
		self.nn = 0

	# Additional Setup
	def setup(self):
		# Publish message from config file, usually a setup msg
		_log.info(self.config['message'])
		super(HPWHWaterDrawAgent, self).setup()

	# Turn water draw solenoid off
	def OFF(self):
		# Set GPIO pin to LOW
		digitalWrite(self.draw, LOW)
		# Publish water draw state
		self.publish_json('waterdraw/state', {}, self.state)

	# Turn water draw solenoid on
	def ON(self):
		# Set GPIO pin to HIGH
		digitalWrite(self.draw, HIGH)
		# Publish water draw state
		self.publish_json('waterdraw/state', {}, self.state)

	# Periodically perform water draws
	@periodic(settings.draw_int)
	def DRAW(self):
		volume = self.config[str(self.nn)]	
		# Calculate time to keep valve open, number is a constant representing
		# the flow rate of the valve (units)
		time_open = volume/1.2
		# Mark the current time
		time_start = time.time()
		dt = 0
		while dt <= time_open:
			# Find elapsed time
			dt = time.time() - time_start
			# Open the valve
			self.state = 1
			self.ON()
		self.state = 0
		self.OFF()
		# Move on to the next water draw value
		self.nn += 1

	# Check for User Input - Water Draw
	@matching.match_start('user/waterdraw')
	# Define the desired temperature
	def define_temp(self, topic, headers, message, match):
		# User Agent published message = [state]
		state_info = jsonapi.loads(message[0])
		self.state = state_info[0]
		# Turn flow off
		if self.state == 0:
			self.OFF()
		# Turn flow on
		elif self.state == 1:
			self.ON()
		# If invalid input, turn flow off
		else:
			self.state = 0
			self.OFF()
#_____________________________________________________________________________#



#________________________________Platform Stuff_______________________________#

# Enable Agent to parse arguments on the command line by the agent launcher
def main(argv=sys.argv):
    # Main method called by the platform.
    utils.default_main(HPWHWaterDrawAgent,
                       description='HPWH Water Draw Agent',
                       argv=argv)

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
