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
Referenced from Kathleen Genger's agent.py code for dehumidifier control as well as ListenerAgent. References from Deepthi Vaidhynathan's communication code also included.


This code was made as a replacement for the controls implemented in a heat pump water heater (HPWH).


'''

'''
-------------------------------------
National Renewable Energy Laboratory
-------------------------------------
NREL is a national laboratory of the U.S. Department of Energy, Office of Energy Efficiency and Renewable Energy, operated by the Alliance for Sustainable Energy, LLC.
NREL-authored documents are sponsored by the U.S. Department of Energy under Contract DE-AC36-08GO28308.

Water-Heater sub Agent: 
**(This agent resides in the water heater platform volttron-v2.0)**
This agent is used to subscribe to control signals from the  SPL volttron-3.0 to water heater throught a port via ZMQ over WiFi. 
This agent along with the waterhheater sub agent is the API comminucation between SPL-Volttronv3.0 amd the water heater

Water heater topics : 

** Control Inputs from SPL volttron to water heater**
wh_control/input/state 
wh_control/input/mode
wh_control/input/deadbands
wh_control/input/temp_desired


**Information request from SPL volttron to water heater**
wh_control/request/state
wh_control/request/mode
wh_control/request/temp_desired
wh_control/request/temp_tank
wh_control/request/deadbands


'''



#____________________________________Setup____________________________________#

# Import Python dependencies
import logging, sys, time, settings, datetime

# Not sure I actually need this
from zmq.utils import jsonapi

# Import VOLTTRON dependencies
from volttron.platform.agent import BaseAgent, PublishMixin, periodic, utils, matching

# Import PyBBIO library for controlling BBB
from bbio import *

# Import Adafruit library for reading thermocouples
import Adafruit_BBIO
import Adafruit_MAX31855.MAX31855 as MAX31855

# Communication imports
from datetime import datetime
import logging
import sys
import json
from . import settings
import time
import zmq


# Enable information and debug logging
utils.setup_logging()
_log = logging.getLogger(__name__)
#_____________________________________________________________________________#

#port setup 
## ip address of SPL volttron-v3.0 platform 
host = "192.168.127.3"
port = "3002"
channel = ""

#____________________________________Agent____________________________________#  
class WHsub(PublishMixin, BaseAgent):

	def __init__(self, config_path, **kwargs):
		super(WHsubAgent, self).__init__(**kwargs)
		self.config = utils.load_config(config_path)

		

	# Additional Setup
	def setup(self):
		# Publish message from config file, usually a setup msg
		_log.info(self.config['message'])
		super(WHsubAgent, self).setup()


  @periodic(settings.HEARTBEAT_PERIOD)
  def publish_heartbeat(self):
    channels = ""
    packet = {}
    packet = socket.recv()
    channels, message = packet.split('~');
    print packet
    messages = json.loads(message)
    msg={}
    topics  = messages['topic']
    msg = messages['message']
    self.publish_json(topics, {}, msg)
      


def main(argv=sys.argv):
    # Main method called by the platform.
    utils.default_main(WHsubAgent,
                       description='HPWH v-2.0 sub Agent',
                       argv=argv)

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass