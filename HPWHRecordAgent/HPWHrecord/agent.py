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
11/1/15
Referenced from Kathleen Genger's agent code for dehumidifier control


This scrip records pertinent data from heat pump water heater (HPWH) testing in a space dilineated text file.

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

# Enable information and debug logging
utils.setup_logging()
_log = logging.getLogger(__name__)
#_____________________________________________________________________________#



#____________________________________Agent____________________________________#  

# Blink an LED based off of input from user and demand agents
class HPWHRecordAgent(PublishMixin, BaseAgent):

	def __init__(self, config_path, **kwargs):
		super(HPWHRecordAgent, self).__init__(**kwargs)

		# load library from config file
		self.config = utils.load_config(config_path)

	# Additional Setup
	def setup(self):
		# Publish message from config file, usually a setup msg
		_log.info(self.config['message'])
		super(HPWHRecordAgent, self).setup()

		# Set up txt file to save data
		# Define the start of test
		now = datetime.datetime.now()
		# Define the file as test_isotime
		#filename = 'test' + now.isoformat()
		filename = 'benderisgreat'
		# Open the file
		self.target = open(filename, 'w')
		# Make sure file is clear
		self.target.truncate()
		# Write Header
		self.target.write('Brian Ruskauff\nNREL\nHPWH Control Test\n%s\n\n' %now)
		self.target.write('TimeStamp    Temp_Lower(F)    Temp_Upper(F)    '
				'Desired_Temp(F)    Power(KW)    Status\n\n')

	# Check for Measurement Input - Temperature
	@matching.match_start('measure/temp')
	def tank_temp(self, topic, headers, message, match):
		# Measure Agent publishes message = [up_temp, low_temp]
		temp_info = jsonapi.loads(message[0])
		self.up_temp = temp_info[0]
		self.low_temp = temp_info[1]

	# Check for User Input - Temperature
	@matching.match_start('user/temp')
	# Define the desired temperature
	def define_temp(self, topic, headers, message, match):
		# User Agent publishes message = [old_temp, new_temp]
		temp_info = jsonapi.loads(message[0])
		self.desired_temp = temp_info[1]

	# Check for Measurement Input - Power
	@matching.match_start('measure/pow')
	def define_pow(self, topic, headers, message, match):
		# Measurement Agent publishes message = [power]
		pow_info = jsonapi.loads(message[0])
		self.power = pow_info[0]

	# Check for Control Input - Mode Status
	@matching.match_start('control/status')
	def define_status(self, topic, headers, message, match):
		# Measurement Agent publishes message = [state, mode, desired_temp]
		status_info = jsonapi.loads(message[0])
		self.status = status_info[1]

	@periodic(settings.record_int)
	# Write Data to txt file
	def write_date(self):
		now = datetime.datetime.now()
		# Write Time Stamp
		self.target.write('%s:%s:%s     ' %(now.hour, now.minute, now.second))
		# Write Lower Tank Temperature
		try:
			self.target.write(str(round(self.low_temp, 3)) + '          ')
		except AttributeError:
			self.target.write('NaN              ')
		# Write Upper Tank Temperature
		try:
			self.target.write(str(round(self.up_temp, 3)) + '          ')
		except AttributeError:
			self.target.write('NaN              ')
		# Write Desired Temperature
		try:
			self.target.write(str(round(self.desired_temp, 3)) + '   '
					'           ')
		except AttributeError:
			self.target.write('NaN                ')
		# Write Power Consumption
		try:
			self.target.write(str(round(self.power, 3)) + '             ')
		except AttributeError:
			self.target.write('NaN          ')
		# Write Status
		try:
			self.target.write(self.status)
		except AttributeError:
			self.target.write('NaN')
		self.target.write('\n')
#_____________________________________________________________________________#



#________________________________Platform Stuff_______________________________#

# Enable Agent to parse arguments on the command line by the agent launcher
def main(argv=sys.argv):
    # Main method called by the platform.
    utils.default_main(HPWHRecordAgent,
                       description='HPWH Record Agent',
                       argv=argv)

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
