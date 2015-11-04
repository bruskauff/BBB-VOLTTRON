from bbio import *

FAN = PWM1A
percent = 80

# analogWrite() must be called before pwmFrequency() will work
analogWrite(Fan, 0)

def loop():
	# Input percent speed
	percent = float(rawinput(
			'What % should I run at? 80% is default.\n>>>'))
	# Determine Hz, range is 30Hz to 30kHz
	hz = (percent/100) * (30000 - 30)/100 + 30
	# Set pwm frequency
	pwmFrequency(FAN, hz)
