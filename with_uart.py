from myhdl import *
from hdl import m_manager, m_dec
from icecua.hdl import rom, bussedram, ram, uart
from icecua.interface import RamBus
from icecua import sim
from pyprind import ProgBar #just for funsies.

sim_time = 100000000
# sim_time = 10000

@block
def with_uart(clk,hex_freq,fpga_rx,fpga_tx,trigger):
	N=9
	sched_len = Signal(intbv(0,min=0,max=128))

	modules = []
	# if __debug__:
	#	period = 10
	#	bar = ProgBar(sim_time/period,width=40,bar_char='X')
	#	modules.append(sim.clkdriver(clk,period))
	#	@always_seq(clk.posedge,reset=None)
	#	def barmonitor():
	#		bar.update()
	#	modules.append(barmonitor)


	#define the schedule
	#note that all these variables are the same length
	set_freq   	= Signal(intbv(0,min=0,max=int(3.2e9))) #in 10s of hertz
	freq_step  	= Signal(intbv(0,min=0,max=int(3.2e9))) #in log10 
	time_step  	= Signal(intbv(0,min=0,max=int(3.2e9))) #clock cycles
	hold_time  	= Signal(intbv(0,min=0,max=int(3.2e9))) #clock cycles
	nothing    	= Signal(intbv(0,min=0,max=int(3.2e9)))
	sched_index	= Signal(intbv(0,min=0)[8:])

	#define the reset signal
	reset = ResetSignal(0,active=1,async=True)

	#define rom-manager handshaking signals
	notclock = Signal(bool(1))
	length_of_signals = len(set_freq)
	start, ready, done = [Signal(bool(0)) for x in range(3)]
	whichram = Signal(intbv(0)[8:])
	biggestblock_l = [Signal(bool(0)) for i in range(length_of_signals)]
	biggestblock = ConcatSignal(*reversed(biggestblock_l))

	#define manager-dec control signals
	curr_freq   = Signal(intbv(0,min=0,max=int(3.2e9)))
	add,sub,dec_clk = [Signal(bool(0)) for x in range(3)]
	incr = Signal(intbv(0)[N:])

	#ram - fsm state stuff
	t_state = enum(
				'READWHICHRAM',
				'PARSEFORRAM',
				'SENDTORAM',
				'RESET'
			)

	state = Signal(t_state.READWHICHRAM)

	#define the uart module and the communications arbiter.
	rx_data = Signal(intbv(0)[8:])
	drdy	= Signal(bool(0))
	
	modules.append(uart(
			clk=clk, 
			rx=fpga_rx,
			tx=fpga_tx,
			reset=None,
			rx_data=rx_data,
			drdy=drdy
		))

	freq_rambus 	= RamBus(typical=intbv(0,min=0,max=int(3.2e9)),depth=128)
	fstep_rambus	= RamBus(typical=intbv(0,min=0,max=int(3.2e9)),depth=128)
	tstep_rambus	= RamBus(typical=intbv(0,min=0,max=int(3.2e9)),depth=128)
	hold_rambus 	= RamBus(typical=intbv(0,min=0,max=int(3.2e9)),depth=128)

	modules.append(bussedram(
			rambus=freq_rambus
		))

	modules.append(bussedram(
			rambus=fstep_rambus
		))

	modules.append(bussedram(
			rambus=tstep_rambus
		))

	modules.append(bussedram(
			rambus=hold_rambus
		))

	# modules.append(ram(
	#		clk=freq_rambus.clk,
	#		din=freq_rambus.din,
	#		dout=freq_rambus.dout,
	#		addr=freq_rambus.addr,
	#		we=freq_rambus.we,
	#		width=freq_rambus.width,
	#		depth=freq_rambus.width
	#	))

	# modules.append(ram(
	#		clk=fstep_rambus.clk,
	#		din=fstep_rambus.din,
	#		dout=fstep_rambus.dout,
	#		addr=fstep_rambus.addr,
	#		we=fstep_rambus.we,
	#		width=fstep_rambus.width,
	#		depth=fstep_rambus.width
	#	))

	# modules.append(ram(
	#		clk=tstep_rambus.clk,
	#		din=tstep_rambus.din,
	#		dout=tstep_rambus.dout,
	#		addr=tstep_rambus.addr,
	#		we=tstep_rambus.we,
	#		width=tstep_rambus.width,
	#		depth=tstep_rambus.width
	#	))

	# modules.append(ram(
	#		clk=hold_rambus.clk,
	#		din=hold_rambus.din,
	#		dout=hold_rambus.dout,
	#		addr=hold_rambus.addr,
	#		we=hold_rambus.we,
	#		width=hold_rambus.width,
	#		depth=hold_rambus.width
	#	))


	@always_comb
	def clockinverter():
		''' Just connect the notclock signal for passing into the RAMs  '''
		notclock.next = not clk

	freq_rambus_addr 	= Signal(intbv(0)[8:])
	fstep_rambus_addr	= Signal(intbv(0)[8:])
	tstep_rambus_addr	= Signal(intbv(0)[8:])
	hold_rambus_addr 	= Signal(intbv(0)[8:])

	@always_seq(clk.posedge,reset=reset)
	def ramwiring():
		''' Connect basic signals of the RAMS: data in and data_out and clock'''
		# biggestblock.next = ConcatSignal(*reversed(biggestblock_l))

		for i in range(32):
			freq_rambus.din.next 	= biggestblock[32:]
			fstep_rambus.din.next	= biggestblock[32:]
			tstep_rambus.din.next	= biggestblock[32:]
			hold_rambus.din.next 	= biggestblock[32:]

		set_freq.next 	= freq_rambus.dout 
		freq_step.next	= fstep_rambus.dout
		time_step.next	= tstep_rambus.dout
		hold_time.next	= hold_rambus.dout 

		freq_rambus.clk.next 	= notclock
		fstep_rambus.clk.next	= notclock
		tstep_rambus.clk.next	= notclock
		hold_rambus.clk.next 	= notclock

		if state == t_state.READWHICHRAM:
			freq_rambus.addr.next 	= sched_index
			fstep_rambus.addr.next	= sched_index
			tstep_rambus.addr.next	= sched_index
			hold_rambus.addr.next 	= sched_index
		else:
			freq_rambus.addr.next 	=	freq_rambus_addr 
			fstep_rambus.addr.next	=	fstep_rambus_addr
			tstep_rambus.addr.next	=	tstep_rambus_addr
			hold_rambus.addr.next 	=	hold_rambus_addr 





	@always(
			freq_rambus.length,
			fstep_rambus.length, 
			tstep_rambus.length, 
			hold_rambus.length,
			drdy)
	def determine_sched_len():
		''' Some nasty combinatorial logic here to determine
		the schedule length'''
		if freq_rambus.length < fstep_rambus.length and freq_rambus.length < tstep_rambus.length and freq_rambus.length < hold_rambus.length:
			sched_len.next = freq_rambus.length
		elif tstep_rambus.length < fstep_rambus.length and tstep_rambus.length < freq_rambus.length and tstep_rambus.length < hold_rambus.length:
			sched_len.next = tstep_rambus.length
		elif hold_rambus.length < fstep_rambus.length and hold_rambus.length < freq_rambus.length and hold_rambus.length < tstep_rambus.length:
			sched_len.next = hold_rambus.length
		else:
			sched_len.next = fstep_rambus.length


	@block
	def comms_arbiter():
		''' Finite State Machine for parsing data from the UART
		into the appropriate latch and then writing to the appropriate 
		RAM'''

		
		latch_counter = Signal(intbv(0)[8:])

		drdy_turnedon = Signal(bool(0))
		drdy_old	 = Signal(bool(0))

		@always_seq(clk.posedge,reset=reset)
		def drdy_monitor():
			''' This is a little block for determining whether 
			drdy has transitioned in the last clock cycle.
			It effectively turns the drdy step function into 
			a hat function.
			'''
			drdy_old.next = drdy
			if drdy != drdy_old and drdy_old == 0:
				drdy_turnedon.next = 1
			else:
				drdy_turnedon.next = 0

		@always_seq(clk.posedge,reset=reset)
		def fsm():
			''' This fsm latches (just after) the dataready positive edge
			signal. The data is guaranteed to be ready then.'''
			if state == t_state.READWHICHRAM and drdy_turnedon:
				freq_rambus.we.next 	= 0
				fstep_rambus.we.next	= 0
				tstep_rambus.we.next	= 0
				hold_rambus.we.next 	= 0
				whichram.next = rx_data
				if rx_data != 255:
					state.next = t_state.PARSEFORRAM
				else:
					state.next = t_state.RESET
			elif state == t_state.PARSEFORRAM and drdy_turnedon:
				latch_counter.next = latch_counter + 1
				for i in range(8):
					biggestblock_l[i+8*latch_counter].next  = rx_data[i]
				if latch_counter == 3:
					latch_counter.next = 0
					state.next = t_state.SENDTORAM
			elif state == t_state.SENDTORAM:
				if whichram == 0:
					freq_rambus.we.next = 1
					freq_rambus.length.next =  freq_rambus.length + 1
					freq_rambus_addr.next = freq_rambus_addr + 1
				elif whichram == 1:
					fstep_rambus.we.next = 1
					fstep_rambus.length.next = fstep_rambus.length.next+ 1
					fstep_rambus_addr.next = fstep_rambus_addr + 1
				elif whichram == 2:
					tstep_rambus.we.next = 1
					tstep_rambus.length.next = tstep_rambus.length + 1
					tstep_rambus_addr.next = tstep_rambus_addr + 1
				elif whichram == 3:
					hold_rambus.we.next = 1
					hold_rambus.length.next = hold_rambus.length + 1
					hold_rambus_addr.next = hold_rambus_addr + 1
				else:
					freq_rambus.we.next 	= 0
					fstep_rambus.we.next	= 0
					tstep_rambus.we.next	= 0
					hold_rambus.we.next 	= 0
				state.next = t_state.READWHICHRAM
			else: 
				# state == t_state.RESET
				reset.next = 1

		return fsm,drdy_monitor

	# freq_rom = rom(
	#	dout=set_freq, 
	#	addr=sched_index,
	#	CONTENT=tuple((int(x) for x in (1e6, 14e6,12e6,2e6)))
	#	)
	# tstep_rom = rom(
	#	dout=time_step, 
	#	addr=sched_index,
	#	CONTENT=tuple((int(x) for x in (14,1,2,1)))
	#	)
	# fstep_rom = rom(
	#	dout=freq_step, 
	#	addr=sched_index,
	#	CONTENT=tuple((int(x) for x in (4,3,2,1)))
	#	)
	# holdt_rom = rom(
	#	dout=hold_time,
	#	addr=sched_index,
	#	CONTENT=tuple((int(x) for x in (1e5,20e5,10e5,1e5)))
	#	)

	manager = m_manager(
			set_freq=set_freq,
			set_step_f=freq_step,
			set_step_t=time_step,
			set_wait=hold_time,
			start=start,
			done=done,
			clk=clk,
			bq=curr_freq,
			add_o=add,
			sub_o=sub,
			incr_o=incr,
			dec_clk=dec_clk,
			ready=ready,
			reset=reset,
			N=N
		)

	dec = m_dec(
			clk=dec_clk,
			add=add,
			sub=sub,
			q=hex_freq,
			bq=curr_freq,
			incr=incr,
			reset=reset,
			N=N
		)

	@always_seq(clk.posedge,reset=reset)
	def schedule_arbiter():
		if ready == True:
			start.next = (1 and (not done)) and trigger
			if sched_index < sched_len - 1:
				sched_index.next = sched_index + 1
			else:
				done.next = 1
		else:
			start.next = 0

	return manager,dec,modules,schedule_arbiter,comms_arbiter(),clockinverter,determine_sched_len,ramwiring
clk = Signal(bool(0))
hex_freq = Signal(intbv(0,min=0,max=int(3.2e9)))
fpga_rx	= Signal(bool(0))
fpga_tx	= Signal(bool(0))
trigger = Signal(bool(0))
inst = with_uart(clk,hex_freq,fpga_rx=fpga_rx,fpga_tx=fpga_tx,trigger=trigger)
inst.convert()
# inst.config_sim(trace=True)
# inst.run_sim(sim_time)
