from myhdl import *

@block
def clkdiv(clk_in,clk_out,freq_in,freq_out):
	'''	clk_in    -- master clock signal
	   	clk_out	  -- new clock output
	   	freq_in	  -- the frequency of the input clock
	   	freq_out  -- the desired frequency of the output clock
	'''
	clk_new = Signal(bool(0))

	if freq_out >= freq_in:
		@always_comb
		def donothing():
			clk_out.next = clk_in

		return donothing
	else:
		counter = Signal( intbv(0,min=0, max=int(freq_in/freq_out)))
		@always_comb
		def wiring():
			clk_out.next = clk_new

		@always_seq(clk_in.posedge,reset=None)
		def clockdivider():
			if counter == counter.max-1 or counter == counter.max//2:
				clk_new.next = not clk_new

			if counter == counter.max-1:    #the integer division
				counter.next = 0
			else:
				counter.next = counter + 1

		return clockdivider,wiring
