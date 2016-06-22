from myhdl import *

@block
def clkdriver(clk,period=10):

	@instance
	def clkgen():
		while True:
			clk.next = 1
			yield delay(period//2)
			clk.next = 0
			yield delay(period - period//2)

	return clkgen