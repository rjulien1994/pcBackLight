# pcBackLight
Transform computer screen into backlight tv

For this project, I used an arduino uno and a neoPixel strip.

The python script capture the screen with pillow and uses simple statistics to "estimate" the value of the color seen on screen.
It maps the color to the corresponding pixel and sends the information as a 1D array to the arduino via serial communication.
The arduino confirms receiving the data every 30 to 36 bytes to not overflow the buffer.

Be aware that for serial communication, the arduino uses an interrupt function which can interfere with other libraries using the internal clocks.
