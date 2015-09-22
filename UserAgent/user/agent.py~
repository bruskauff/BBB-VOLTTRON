'''
Brian Ruskauff
National Renewable Energy Labs (NREL)
9/19/15
Referenced from Kathleen Genger's agent.py code for user control


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
class UserAgent(PublishMixin, BaseAgent):
	'''Allows user to broadcase messages for BBB control directly from a 		computer on a different network'''
	
	# Initialize attributes
	def __init__(self, config_path, **kwargs):
		super(UserAgent, self).__init__(**kwargs)
		'''# Config file includes socket location info
		self.config = utils.load_config(config_path)'''
		self.config = {'address': ('127.0.0.1', 7575), 'backlog': 5}
		# Initialize running variable
		self.running = False
		self.state = False
		self.interval = 0

	# Additional Setup
	def setup(self):
		_log.info('Setting up User Input Agent...')
		# Always call the base class setup()
		super(UserAgent, self).setup()
		# Open a socket to listen for incoming connections
		self.ask_socket = sock = socket.socket()
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind(tuple(self.config['address']))
		sock.listen(int(self.config['backlog']))
		# Register a callback to accept new connections
		self.reactor.register(self.ask_socket, self.handle_accept)

	# Send current state and ask for a new one
	def ask_input(self, file):
		file.write('\nCurrent state: %r.\nCurrent interval: %r.\n Enter new 				command: ' %(self.state, self.interval))
		
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

	# Change state and notify other agents
	def state_change(self, state):
		# Assign old & new state
		old_state, self.state = self.state, state
		# Publish new state via VOLTTRON
		self.publish_json('user/state', {}, (old_state, self.state))

	# Change state and notify other agents
	def interval_change(self, interval):
		# Assign old & new interval
		old_interval, self.interval = self.interval, interval
		# Publish new state via VOLTTRON
		self.publish_json('user/interval', {}, (old_interval, self.interval))

	# Returns to demand-response mode
	def return_to_normal(self):
		msg = 'return'
		self.publish_json('user/mode', {}, msg)

	# Receive new state from user and ask for another'''
	def handle_input(self, file):
		try:
			response = file.readline()
			if not response:
				raise socket.error('disconnected')
			response = response.strip() #strip gets rid of end line character
			# If there is a valid response
			if response:
				# Turn LED blinking off
				if response == 'OFF':
					self.change_state(response)
				# Turn LED blinking on
				elif response == 'ON':
					self.state_change(response)
				# Change blinking interval
				elif isinstance(response, float) == True:
					self.interval_change(response)
				# Change blinking interval
				elif isinstance(response, int) == True:
					self.interval_change(response)
				# Allow LED to respond to demand agent
				elif response == 'return':
					self.return_to_normal()
				# Update status information
				elif response == 'status':
					self.ask_input()
		except socket.error:
			_log.info('Connection {} disconnected'.format(file.fileno()))
			self.reactor.unregister(file)
#_____________________________________________________________________________#



#___________________________________Cleanup___________________________________#
def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.default_main(UserAgent, description='Gives Direct Control', argv=argv)
    except Exception as e:
        _log.exception('unhandled exception')


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
