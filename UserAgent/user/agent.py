

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
        self.publish_json('powercost/demandagent', {}, self.cost_level)
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
