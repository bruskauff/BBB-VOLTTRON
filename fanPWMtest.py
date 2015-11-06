from bbio import *

FAN = 'PWM1A'#Pin P9.14

# Initialize pin at 0 duty cycle
analogWrite(FAN, 0)
# Set frequency to 30,000 Hz
pwmFrequency(FAN, 15000)

while True:
	# Input percent speed
	percent = float(raw_input(
			'\nWhat percent should I run at?\nTyp: 85%.\n'
			'>>>'))
	duty = 255*percent/100
	# Set pwm frequency
	analogWrite(FAN, duty)
