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
10/30/15
References from Kathleen Genger's Dehumidifier Control Code


Measurement Agent
This script reads and publishes temperature of a heat pump water heater (HPWH) as well as power consumption. Two T-type thermocouples are read using MAX31855 Adafruit breakout boards. The boards are linearized for K-type thermocouples so this code relinearizes for T-type. Temperature is stabilized using a moving average with parameters defined in the setting.py file. The power signal is given as a 10V signal. Using 5k and 1k resistors as a voltage divider the signal is read from 0-1.7V.

INPUT 
	-No software inputs
OUTPUT
	- when outputting tank temperature
		- topic = 'measure/temp'
		- message = [temp_up, temp_low]
	- when outputting power consumption
		- topic = 'measure/pow'
		- message = [power]
'''
#_____________________________________________________________________________#



#____________________________________Setup____________________________________#

# Import Python dependencies
import logging, sys, settings

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

# Measure tank temp and water heater power 
class HPWHMeasureAgent(PublishMixin, BaseAgent):

	def __init__(self, config_path, **kwargs):
		super(HPWHMeasureAgent, self).__init__(**kwargs)

		# Load library from config file
		self.config = utils.load_config(config_path)

		# Make variables for ADC Pins
		self.ADC = AIN4

		# Set up pins for SPI interface, thermocouple readings
		CLK = 'P9_12'
		CS = 'P9_15'
		DO = 'P9_23'
		self.sensor_up = MAX31855.MAX31855(CLK, CS, DO)
		'''
		CLK = 'P9_12'
		CS = 'P9_15'
		DO = 'P9_23'
		self.sensor = MAX31855.MAX31855(CLK, CS, DO)
		'''

		# nn is a placeholder for list operations
		self.nn = 0
		# ii is total samples to keep in moving avg. time*samplerate
		self.ii = settings.seconds * 1 / settings.temp_int
		# Initialize empty values lists
		self.values_up = [0]*int(self.ii)
		self.values_low = [0]*int(self.ii)

	# Additional Setup
	def setup(self):
		# Publish message from config file, usually a setup msg
		_log.info(self.config['message'])
		super(HPWHMeasureAgent, self).setup()

	@periodic(settings.temp_int)
	# Measure tank temperature, perform moving average for stability
	def measure_temp(self):
		# Read temp and convert to Fahrenheit
		temp_up = self.sensor_up.readTempC() * 9 / 5 + 32
		#temp_low = self.sensor_low.readTempC() * 9 / 5 + 32
		# Add newest temp reading to list
		self.values_up[self.nn] = temp_up
		#self.values_low[self.nn] = temp_low
		# Find average in value lists
		self.temp_up = sum(self.values_up)/len(self.values_up)
		#self.temp_low = sum(self.values_low)/len(self.values_low)
		self.nn += 1
		# Reset nn when at end of list
		if self.nn == self.ii:
			self.nn = 0

	@periodic(settings.pub_temp_int)
	# Publish tank temperature
	def publish_temp(self):
		try:
			self.publish_json('measure/temp', {}, (self.temp_up))#, 
					#self.low_temp)) 
		except:
			return

	@periodic(settings.pow_int)
	# Measure power consumption
	def measure_pow(self):
		# AnalogRead gives a number in millivolts
		mV = analogRead(self.ADC)
		# Scale millivolts to power (watts)
		self.power = (1000/1.73) * mV * 1000
		

	@periodic(settings.pub_pow_int)
	# Publish power consumption
	def publish_pow(self):
		try:
			self.publish_json('measure/pow', {}, (self.power))
		except:
			return
#_____________________________________________________________________________#



#________________________________Platform Stuff_______________________________#

# Enable Agent to parse arguments on the command line by the agent launcher
def main(argv=sys.argv):
    # Main method called by the platform.
    utils.default_main(HPWHMeasureAgent,
                       description='HPWH Measurement Agent',
                       argv=argv)

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
