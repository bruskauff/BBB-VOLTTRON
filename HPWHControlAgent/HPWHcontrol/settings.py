'''
Calculation Interval must be larger than the Publish Interval. Publish Interval must also be a factor of the Calculation Interval. When using this code with the Blinking LED Agent the publish interval must be as small as the shortest possible interval (currently 0.02 seconds)
'''

interval = 5
CALCULATION_INTERVAL = 10
PUBLISH_INTERVAL = .02
