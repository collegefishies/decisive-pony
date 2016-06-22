from myhdl import *
from hdl import m_manager, m_dec
from icecua.hdl import rom
from icecua import sim
from pyprind import ProgBar #just for funsies.

sim_time = 100000000
sim_time = 10000

@block
def test(clk,hex_freq):
	N=9
	sched_len = 4

	modules = []
	if __debug__:
		period = 10
		bar = ProgBar(sim_time/period,width=40,bar_char='█')
		modules.append(sim.clkdriver(clk,period))
		@always_seq(clk.posedge,reset=None)
		def barmonitor():
			bar.update()
		modules.append(barmonitor)


	#define the schedule
	set_freq   	= Signal(intbv(0,min=0,max=int(3.2e9))) #in 10s of hertz
	freq_step  	= Signal(intbv(0,min=0,max=int(3.2e9))) #in log10 
	time_step  	= Signal(intbv(0,min=0,max=int(3.2e9))) #clock cycles
	hold_time  	= Signal(intbv(0,min=0,max=int(3.2e9))) #clock cycles
	nothing    	= Signal(intbv(0,min=0,max=int(3.2e9)))
	sched_index	= Signal(intbv(0,min=0)[8:])

	#define rom-manager handshaking signals
	start, ready, done = [Signal(bool(0)) for x in range(3)]
	#define manager-dec control signals
	add,sub,dec_clk = [Signal(bool(0)) for x in range(3)]
	incr = Signal(intbv(0)[N:])

	freq_rom = rom(
		dout=set_freq, 
		addr=sched_index,
		CONTENT=tuple((int(x) for x in (1e6, 14e6,12e6,2e6)))
		)
	tstep_rom = rom(
		dout=time_step, 
		addr=sched_index,
		CONTENT=tuple((int(x) for x in (14,1,2,1)))
		)
	fstep_rom = rom(
		dout=freq_step, 
		addr=sched_index,
		CONTENT=tuple((int(x) for x in (4,3,2,1)))
		)
	holdt_rom = rom(
		dout=hold_time,
		addr=sched_index,
		CONTENT=tuple((int(x) for x in (1e5,20e5,10e5,1e5)))
		)

	manager = m_manager(
			set_freq=set_freq,
			set_step_f=freq_step,
			set_step_t=time_step,
			set_wait=hold_time,
			start=start,
			done=done,
			clk=clk,
			add_o=add,
			sub_o=sub,
			incr_o=incr,
			dec_clk=dec_clk,
			ready=ready,
			reset=None,
			N=N
		)

	dec = m_dec(
			clk=dec_clk,
			add=add,
			sub=sub,
			q=hex_freq,
			incr=incr,
			reset=None,
			N=N
		)

	@always_seq(clk.posedge,reset=None)
	def arbiter():
		if ready == True:
			start.next = 1 and not done
			if sched_index < sched_len - 1:
				sched_index.next = sched_index + 1
			else:
				done.next = 1
		else:
			start.next = 0

	return manager,dec,freq_rom,tstep_rom,fstep_rom,holdt_rom,modules,arbiter
clk = Signal(bool(0))
hex_freq = Signal(intbv(0,min=0,max=int(3.2e9)))
inst = test(clk,hex_freq)
inst.config_sim(trace=True)
inst.run_sim(sim_time)
