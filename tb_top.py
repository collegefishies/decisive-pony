# -*- coding: utf-8 -*-

from myhdl import *
from icecua.sim import clkdriver
from fractions import Fraction
from math import log10,floor
from with_uart import with_uart
from pyprind import ProgBar #just for funsies.

baud_clk = Signal(False)
fpga_rx = Signal(False)
freq_old = 0
freq_new = 0
time_old = 0

clock_frequency = int(12e6)
baud_frequency = 9600

ns = 1e-9
in_ns = 1./ns
in_clk_cycles = clock_frequency
waittime = 8*10*clock_frequency/baud_frequency*in_ns

sim_time = int(400e-3*in_ns)
@block
def pc_uart(baud_clk,pc_tx,address,data,when):

	@instance
	def writebytes():
		yield delay(int(when))
		for i in range(8):
			yield baud_clk.posedge
			pc_tx.next = address[i]
		yield baud_clk.posedge
		pc_tex.next = 1
		yield baud_clk.posedge
		pc_tex.next = 1
		for byte in range(len(data)/8):
			for i in range(8):
				yield baud_clk.posedge
				pc_tx.next = data[i + 8*byte]
			yield baud_clk.posedge
			pc_tex.next = 1
			yield baud_clk.posedge
			pc_tex.next = 1

	return writebytes

@block
def write_freq(freq,when):
	global freq_old,freq_new
	freq_new = freq
	address = intbv(0)[8:]
	data = intbv(int(freq),min=0,max=int(3.2e9))

	return pc_uart(baud_clk,pc_tx=fpga_rx,address=address,data=data,when=when)

@block
def write_time(time,when):
	global freq_old,freq_new,time_old,time_new
	fstep_address = intbv(1)
	tstep_address = intbv(2)
	
	rate = (freq_new - freq_old)/((time - time_old)*in_ns)

	f_rate = Fraction(1/rate).limit_denominator(1000)
	f_step = f_rate.denominator
	t_step = f_rate.numerator

	t_step_in_clk_cycles = intbv(int(t_step*ns*clock_frequency))

	f_step_in_log10 = intbv(int(log10(f_step)))

	time_old = time
	freq_old = freq_new

	waittime = 8*10*clock_frequency/baud_frequency*in_ns
	stimulus = []
	stimulus.append(pc_uart(baud_clk,fpga_rx,fstep_address,data=f_step_in_log10,when=when))
	stimulus.append(pc_uart(baud_clk,fpga_rx,tstep_address,data=t_step_in_clk_cycles,when=(when+waittime)))

	return stimulus

@block 
def write_hold(time,when):
	hold_address = intbv(3)

	data = intbv(time*in_clk_cycles)

	return pc_uart(baud_clk,fpga_rx,address=hold_address,data=data,when=when)

@block
def trigger_signal(baud_clk,trigger,when):

	@instance
	def trigger_it():
		yield delay(int(when))
		trigger.next = 1
		yield baud_clk.posedge
		trigger.next = 0

	return trigger_it


#############################################
######         Scripting Time          ######
#############################################


@block
def testbench():
	modules = []

	clk = Signal(False)
	trigger = Signal(False)
	fpga_tx = Signal(False)

	if __debug__:
		bar = ProgBar(sim_time,width=40,bar_char='█')
		@always_seq(clk.posedge,reset=None)
		def barmonitor():
			bar.update()
			if now() % 50000 == 0 and now():
				print now()
		modules.append(barmonitor)

	hex_freq = Signal(intbv(0,min=0,max=int(3.2e9)))
	amphenol = Signal(intbv(0)[50:])

	uut = top(clk,trigger,fpga_rx,fpga_tx,amphenol)

	clk_driver = clkdriver(clk=clk,period=int(1./clock_frequency)*in_ns)
	baud_driver = clkdriver(clk=baud_clk,period=int(1./baud_frequency)*in_ns)

	stimulus = []

	#write first schedule point
	stimulus.append(write_freq(freq=25.4e6,when=100))
	stimulus.append(write_time(time=1e-6,when=100+waittime))
	stimulus.append(write_hold(time=0,when=100+2*waittime))

	#write second schedule point
	stimulus.append(write_freq(freq=27.7e6,when=100+3*waittime))
	stimulus.append(write_time(time=100e-3,when=100+4*waittime))
	stimulus.append(write_hold(time=0,when=100+5*waittime))
	
	#write third schedule point
	stimulus.append(write_freq(freq=28.4e6,when=100+6*waittime))
	stimulus.append(write_time(time=300e-3,when=100+7*waittime))
	stimulus.append(write_hold(time=0,when=100+8*waittime))

	#trigger
	stimulus.append(trigger_signal(baud_clk,trigger,when=100+9*waittime))
	return uut,stimulus,clk_driver,baud_driver,modules


tb = testbench()

tb.config_sim(trace=True)
tb.run_sim(sim_time)