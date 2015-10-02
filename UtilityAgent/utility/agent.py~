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
Referenced from Kathleen Genger's agent.py code for dehumidifier control as well as Lists


This script was made to output energy costs that fluctuate. It is specifically designed to work with a blinking LED so many things are hard coded and not too realistic. 

It initially runs with a medium energy cost of $0.14. It will output the energy cost every 0.02 seconds(to keep up with the Blinking LED Agent's max speed) and it will change the cost at randome every 10 seconds.

INPUT 
	- no input is required
OUTPUT
	- logs the current cost level and price
		- topic = 'powercost/demandagent'
		- message = (cost_level, cost)
'''
#_____________________________________________________________________________#



#____________________________________Setup____________________________________#
# Import python modules
import logging, sys, time

# Import volttron modules
from volttron.platform.agent import BaseAgent, PublishMixin, periodic, utils, matching
from volttron.platform.messaging import headers as headers_mod

# Import settings from settings.py file
import settings

# Initialize logging utility
utils.setup_logging()
_log = logging.getLogger(__name__)
#_____________________________________________________________________________#



#____________________________________Agent____________________________________#
class UtilityAgent(PublishMixin, BaseAgent):
    #Randomly chooses a price and price level and publishes power cost info
    #at a rate specified in the settings module

	def __init__(self, config_path, **kwargs):
		super(UtilityAgent, self).__init__(**kwargs)
		# Load configuration libray from config file
		self.config = utils.load_config(config_path)

	def setup(self):
		# Publish startup message from config file
		_log.info(self.config['message'])
		super(UtilityAgent, self).setup()

	# Periodically publish the cost and cost_level
	@periodic(settings.pub_int)
	# Randomly choose a new cost and cost level
	def determine_cost(self):
		hour = time.localtime().tm_hour
		self.cost_level = self.config[str(hour)]
		self.cost = self.config[str(self.cost_level)]

		# Publish (topic, headers, message) to VOLTTRON  
		self.publish_json(
				'utility/cost_info', {}, (self.cost_level, self.cost))

#_____________________________________________________________________________#



#________________________________Always Include_______________________________#
def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.default_main(UtilityAgent, description='Power Cost', argv=argv)
    except Exception as e:
        _log.exception('unhandled exception')


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
