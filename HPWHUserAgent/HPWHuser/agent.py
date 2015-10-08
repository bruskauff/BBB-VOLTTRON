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
9/19/15
Referenced from Kathleen Genger's agent.py code for user control

Connect to the agent using one of the following commands:
    nc 127.0.0.1 7575
    netcat 127.0.0.1 7575
    socat - TCP-CONNECT:127.0.0.1:7575
    telnet 127.0.0.1 7575

This script was made to allow a user to directly control the blinking rate of an LED connected to a BeagleBone Black. It also allows the user to make the flashing stop and start, but it will not explicitly allow the user to keep the LED on or off. This can be simulated by using a low or high interval respectively.

INPUT 
	- signal from DemandAgent with message = [costlevel, cost]
		- costlevel is 'high', 'medium', or 'low'
		- cost is a float in dollars
	- signal from UserAgent with [state, interval]
		- state is 'ON' or 'OFF'
		- interval
OUTPUT
	- when changing the state
		- topic = 'user/state'
		- message = [old_state new_state]
	- when changing the interval
		- topic = 'user/interval'
		- message = [old_interval new_interval]
	- when handing control to automatic based on demand
		- topic = 'user/mode'
		- message = 'return'
'''
#_____________________________________________________________________________#



#____________________________________Setup____________________________________#

# Import required modules
import logging, sys, datetime, socket
from volttron.platform.agent import BaseAgent, PublishMixin, periodic, utils
from zmq.utils import jsonapi

# Setup logging
utils.setup_logging()
_log = logging.getLogger(__name__)
#_____________________________________________________________________________#



#____________________________________Agent____________________________________#

class HPWHUserAgent(PublishMixin, BaseAgent):
	'''Allows user to broadcase messages for BBB control directly from a
			computer on a different network'''
	
	# Initialize attributes
	def __init__(self, config_path, **kwargs):
		super(HPWHUserAgent, self).__init__(**kwargs)
		'''# Config file includes socket location info
		self.config = utils.load_config(config_path)'''
		self.config = {'address': ('127.0.0.1', 7575), 'backlog': 5}
		self.state = False
		self.temp = 100

	# Additional Setup
	def setup(self):
		_log.info('Setting up User Input Agent...')
		# Always call the base class setup()
		super(HPWHUserAgent, self).setup()
		# Open a socket to listen for incoming connections
		self.ask_socket = sock = socket.socket()
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind(tuple(self.config['address']))
		sock.listen(int(self.config['backlog']))
		# Register a callback to accept new connections
		self.reactor.register(self.ask_socket, self.handle_accept)

	# Send current state and ask for a new one
	def ask_input(self, file):
		file.write('\nRunning: %s.\nCurrent temp: %r.\n\n>>>'
				%(self.state, self.temp))
		
	# Accept new connections
	def handle_accept(self, ask_sock):
		sock, addr = ask_sock.accept()
		file = sock.makefile('r+', 0)
		'''_log.info('Connection %r accepted from %r: %r' %(file.fileno(), *addr))'''
		try:
			self.ask_input(file)
		except socket.error:
			_log.info('Connection %r disconnected' %file.fileno())
		# Register a callback to receive input from the client.
		self.reactor.register(file, self.handle_input)

	# Change temp and notify other agents
	def temp_change(self, temp):
		# Assign old & new temp
		old_temp, self.temp = self.temp, temp
		# Publish new state via VOLTTRON
		self.publish_json('user/temp', {}, (old_temp, self.temp))

	# Change state and notify other agents
	def state_change(self, state):
		# Assign old & new state
		old_state, self.state = self.state, state
		# Publish new state via VOLTTRON
		self.publish_json('user/state', {}, (old_state, self.state))

	# Input simulated tank temperatures
	def sim_temp(self, top_temp, bot_temp):
		# Publish simulated temperatures via VOLTTRON
		self.publish_json('user/sim_temp', {}, (top_temp, bot_temp))

	# Receive new state from user and ask for another'''
	def handle_input(self, file):
		try:
			response = file.readline()
			if not response:
				raise socket.error('disconnected')
			response = response.strip() #strip gets rid of end line character
			# If there is a valid response
			if response:
				# Turn the water heater off
				if response == 'off':
					self.state_change(False)
					file.write('\nTurning HPWH off...\n\n>>>')
				# Turn the water heater on
				elif response == 'on':
					self.state_change(True)
					file.write('\nTurning HPWH on...\n\n>>>')
				# Change desired temperature
				elif response == 'temperature':
					file.write('\nRedefine new temperature.\n\n>>>')
					temp = float(file.readline())
					self.temp_change(temp)
					file.write('\nNew temperature set to: %r F.\n\n>>>' 
							%temp)
				# Chnage the simulated temperature
				elif response == 'simulate':
					file.write('\nDefine upper tank temperature.\n\n>>>')
					top_temp = float(file.readline())
					file.write('\nDefine lower tank temperature.\n\n>>>')
					bot_temp = float(file.readline())
					self.sim_temp(top_temp, bot_temp)
					file.write('\nUpper temp: %r F\nLower temp: %r F.\n\n>>>'
							%(top_temp, bot_temp))
				# Update status information
				elif response == 'status':
					self.ask_input(file)
				else:
					file.write('\n** FAILED **\nValid commands are...\n'
							'| on | off | temperature | simulate | status'
									' |\n\n>>>')
		except socket.error:
			_log.info('Connection {} disconnected'.format(file.fileno()))
			self.reactor.unregister(file)
#_____________________________________________________________________________#



#___________________________________Cleanup___________________________________#

def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.default_main(HPWHUserAgent, description='Gives Direct Control', argv=argv)
    except Exception as e:
        _log.exception('unhandled exception')


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
