# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright (c) 2013, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#

# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization
# that has cooperated in the development of these materials, makes
# any warranty, express or implied, or assumes any legal liability
# or responsibility for the accuracy, completeness, or usefulness or
# any information, apparatus, product, software, or process disclosed,
# or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does
# not necessarily constitute or imply its endorsement, recommendation,
# r favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830

#}}}

#____________________________________Setup____________________________________#
import logging, sys, random, datetime

from volttron.platform.agent import BaseAgent, PublishMixin, periodic, utils, matching
from volttron.platform.messaging import headers as headers_mod

import settings

utils.setup_logging()
_log = logging.getLogger(__name__)
#_____________________________________________________________________________#



#____________________________________Agent____________________________________#
class DemandAgent(PublishMixin, BaseAgent):
    #Randomly chooses a price and price level and publishes power cost info
    #at a rate specified in the settings module

    total_t = 0

    def __init__(self, config_path, **kwargs):
        super(DemandAgent, self).__init__(**kwargs)
        self.config = utils.load_config(config_path)
        self.cost = 0.14
        self.cost_level = 'medium'
        self.pub_int = settings.PUBLISH_INTERVAL
        self.calc_int = settings.CALCULATION_INTERVAL

    def setup(self):
        # Demonstrate accessing a value from the config file
        _log.info(self.config['message'])
        self._agent_id = self.config['agentid']
        # Always call the base class setup()
        super(DemandAgent, self).setup()

    @periodic(settings.PUBLISH_INTERVAL)
    def random_cost(self):    
        self.publish_json(
                'powercost/demandagent', {}, (self.cost_level, self.cost))
        DemandAgent.total_t = DemandAgent.total_t + self.pub_int
        _log.info('total_t is %r' %DemandAgent.total_t)
        if round(DemandAgent.total_t) == round(self.calc_int):
            self.cost = (random.randint(10, 16))/100.00
            if self.cost >= 0.10 and self.cost < 0.12:
                self.cost_level = 'low'
            elif self.cost >= 0.12 and self.cost <= 0.14:
                self.cost_level = 'medium'
            elif self.cost > 0.14 and self.cost <= 0.16:
                self.cost_level = 'high'
            DemandAgent.total_t = 0
#_____________________________________________________________________________#



#___________________________________Cleanup___________________________________#
def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.default_main(DemandAgent, description='Simulates demand costs', argv=argv)
    except Exception as e:
        _log.exception('unhandled exception')


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
