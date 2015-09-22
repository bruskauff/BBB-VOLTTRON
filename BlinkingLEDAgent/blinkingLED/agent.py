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


#___________________________________Setup___________________________________#

# Import Statements
import logging, sys, time

from zmq.utils import jsonapi
from volttron.platform.agent import BaseAgent, PublishMixin, periodic, utils, matching

from bbio import *	# for BBB, uses PyBBIO module

# Enable information and debug logging
utils.setup_logging()
_log = logging.getLogger(__name__)
#_____________________________________________________________________________#



#____________________________________Agent____________________________________#  

# Create a class with the convention <Name>Agent & always include PublishMixin # and BaseAgent as its arguments
class BlinkingLEDAgent(PublishMixin, BaseAgent):

	#Initialize class time variables for on and off
	t = time.time()


	def __init__(self, config_path, **kwargs):
		super(BlinkingLEDAgent, self).__init__(**kwargs)
		self.config = utils.load_config(config_path)

		# Make variables for GPIO Pins
		self.LED1 = GPIO1_28 #P9_12

		# Initialize GPIO pin mode
		pinMode(self.LED1, OUTPUT)

		# Initialize output pins to LOW (off)
		digitalWrite(self.LED1, LOW)

		# Initialize LED status to off
		self.LED_status = False

		# Initialize reset varible to True
		self.reset = True

	def setup(self):
		# Demonstrate accessing a value from the config file
		_log.info(self.config['message'])
		self._agent_id = self.config['agentid']
		super(BlinkingLEDAgent, self).setup()

	def LED1_ON(self):
		# Turn on LED1
		digitalWrite(self.LED1, HIGH)

	def LED1_OFF(self):
		# Turn off LED1
		digitalWrite(self.LED1, LOW)

	# Check for Demand Agent Activity
	@matching.match_start('powercost/demandagent')
	def define_interval(self, topic, headers, message, match):
		# Utilities Agent publishes message = [cost_level, cost]
		cost_info = jsonapi.loads(message[0])
		cost_level = cost_info[0]
		cost = cost_info[1]

		# Decide what rate to flash the LED at based on cost level
		if cost_level == 'high':
			self.interval = 5 # 5 seconds between flashes
		elif cost_level == 'medium':
			self.interval = 1 # 1 second between flashes
		elif cost_level == 'low':
			self.interval = 0.25 # 1/4 second between flashes
		else:
			self.interval = 0.02 # If input isn't valid

		# Log information & action
		_log.info("Cost level is %s at $%s, setting interval to %r seconds." %
				(cost_level, cost, self.interval))

		# Deal with LED being on
		if self.LED_status == True and self.reset == True:
			# Reset global t variable to now
			BlinkingLEDAgent.t = time.time()
			self.reset = False

		# Calculate how long LED has been on
		t_diff_on = time.time() - BlinkingLEDAgent.t
		# Will only keep LED on for .0625, HARD #
		if t_diff_on >= .0625 and self.LED_status == True:
			# Turn LED off
			self.LED1_OFF()
			self.LED_status = False
			self.reset = True

		#Deal with LED being off
		if self.LED_status == False and self.reset == True:
			# Reset global t variable to now
			BlinkingLEDAgent.t = time.time()
			self.reset = False
			
		t_diff_off = time.time() - BlinkingLEDAgent.t
		# Keep LED off for interval time
		if t_diff_off >= self.interval and self.LED_status == False:
			# Turn LED on
			self.LED1_ON()
			self.LED_status = True
			self.reset = True
#_____________________________________________________________________________#



#___________________________________Closure___________________________________#

# Enable Agent to parse arguments on the command line by the agent launcher
def main(argv=sys.argv):
    # Main method called by the platform.
    utils.default_main(BlinkingLEDAgent,
                       description='Blinking LED Agent',
                       argv=argv)

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
