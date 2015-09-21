

#____________________________________Setup____________________________________#
# Import required modules
import logging, sys, datetime
from volttron.platform.agent import BaseAgent, PublishMixin, periodic, utils, matching
from volttron.platform.messaging import headers as headers_mod

# Setup logging
utils.setup_logging()
_log = logging.getLogger(__name__)
#_____________________________________________________________________________#



#____________________________________Agent____________________________________#
class DemandAgent(PublishMixin, BaseAgent):
    '''Allows user to broadcase messages for BBB control directly from a 		computer on a different network'''

    def __init__(self, config_path, **kwargs):
		'''Initialize attributes'''
        super(UserAgent, self).__init__(**kwargs)
		# Config file includes socket location info
        self.config = utils.load_config(config_path)
		# Initialize running variable
		self.running = False
		self.state = False
		self.interval = 0

    def setup(self):
        '''Additional Setup.'''
        _log.info('Setting up User Input Agent...')
        # Always call the base class setup()
        super(DemandAgent, self).setup()
		# Open a socket to listen for incoming connections
		self.ask_socket = sock = socket.socket()
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind(tuple(self.config['address']))
		sock.listen(tuple(self.config['backlog']))
		# Register a callback to accept new connections
		self.reactor.register(self.ask_socket, self.handle_accept)

	def ask_input(self, file)
		'''Send current state and ask for a new one'''
		file.write('\nCurrent state: %r.\nCurrent interval: %r.\n Enter new command: ' %(self.state, self.interval))
		
	def handle_accept(self, ask_sock)
		'''Accept new connections'''
		sock, addr = ask_sock. accept()
		file = sock.makefile('r+', 0)
		_log.info('Connection %r accepted from %r: %r' %(file.fileno(), *addr))
		try
			self.ask_input(file)
		except socket.error:
			_log.info('Connection %r disconnected' %file.fileno())
		# Register a callback to receive input from the client.
		self.reactor.register(file, self.handle_input)

	def change_state(self, state)
		'''Change state and notify other agents'''
		# Assign old & new state
		old_state, self.state = self.state, state
		# Publish new state via VOLTTRON
		self.publish_json('user/state', {}, (old_state, self.state)

	def change_interval(self, interval)
		'''Change interval and notify other agents'''
		# Assign old & new interval
		old_interval, self.interval = self.interval, interval
		# Publish new interval via VOLTTRON
		self.publish_json('user/interval', {}, (old_interval, self.interval)

	def return_to_normal(self)
		'''Returns to demand-response mode'''
		self.publish_json('user/mode', {}, 'return')

	def handle_input(self, file)
		'''Receive new state from user and ask for another'''
		try:
			response = file.readline()
			if not response:
				raise socket.error('disconnected')
			response = response.strip() #strip gets rid of end line character
			# If there is a valid response
			if response:
				if response == 'OFF':
					self.change_state(response)
				elif response == 'ON':
					self.change_state(response)
				elif isinstance(response, float) == True:
					self.change_interval(response)
				elif isinstance(response, int) == True:
					self.change_interval(response)
				elif response == 'return':
					self.return_to_normal()
				elif response == 'status':
					self.ask_input()
		
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
