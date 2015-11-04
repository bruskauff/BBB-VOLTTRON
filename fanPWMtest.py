from bbio import *

FAN = 'PWM1A'#Pin P9.14

# Initialize pin at 0 duty cycle
analogWrite(FAN, 0)
# Set frequency to 30,000 Hz
pwmFrequency(FAN, 30000)

while True:
	# Input percent speed
	percent = float(raw_input(
			'\nWhat % should I run at?\n100 = 3700 rpm.\n'
			'>>>'))
	duty = 255*percent/100
	# Set pwm frequency
	analogWrite(FAN, duty)
