from myhdl import *

@block
def m_manager(
	#inputs
	set_freq, set_step_f,set_step_t, set_wait, start, done,
	clk,reset,
	#control inputs
	bq,
	#outputs
		#m_dec control signals
	add_o,sub_o,incr_o,dec_clk,
		#signals
	ready,
	N=10
	):

	''' m_manager -- controller for driving m_dec for a PTS driver
	inputs --
	set_freq  	#desired frequency
	set_step_f	#the logarithm10 of each frequency step (0,1,2,3... -> 1,10,100...)
	set_step_t	#time to wait (in clock cycles) until next frequency step
	set_wait  	#the time (in clock cycles) that this frequency is held until reached
	start     	#an outside signal that says the data in the ^ above
	          	#ports is ready to be read
	done      	#when the FIFO that holds the above values is empty.
	clk       	#the clock signal.
	reset     	#reset signal, how you want it to be activated is not my choice
	add_o     	#the add enable for m_dec
	sub_o     	#the sub enable for m_dec
	incr_o    	#the digit we increment. 
	dec_clk   	#the "clk" for m_dec, it could just be used as an edge activated enable
	ready     	#says we're ready for the next datapoint
	'''

	#define latches
	curr_freq       	= Signal(intbv(0,min=-10**N, max = 10**N))
	set_freq_latch  	= Signal(intbv(0,min=-10**N, max = 10**N))
	set_step_f_latch	= Signal(intbv(0,min=0,max=10**N)) 
	set_step_t_latch	= Signal(intbv(0,min=0,max=10**N))
	set_wait_latch  	= Signal(intbv(0,min=0,max=10**N)) #hold time

	set_freq_latch_int  	= Signal(intbv(0,min=-10**N, max = 10**N))
	set_step_f_latch_int	= Signal(intbv(0,min=-10**N,max=10**N)) 
	set_step_t_latch_int	= Signal(intbv(0,min=-10**N,max=10**N))
	set_wait_latch_int  	= Signal(intbv(0,min=-10**N,max=10**N)) #hold time

	#define internal enables
	frequency_controller_en	= Signal(bool(0))
	waiter_en              	= Signal(bool(0))

	#define state type for finite state machine
	t_state = enum('WAIT','REACH_DESIRED','REACH_DESIRED_CHANGE_STEP','HOLD_FREQ')
	quit                  	= Signal(bool(0))
	start_holding         	= Signal(bool(0))
	quit_turnedon         	= Signal(bool(0))
	start_holding_turnedon	= Signal(bool(0))

	#define initial condition
	state = Signal(t_state.WAIT)

	#define the signals the frequency reacher will toggle
	add_o_int  	= Signal(bool(0))
	sub_o_int  	= Signal(bool(0))
	dec_clk_int	= Signal(bool(0))


	@always(start.posedge)
	def latcher():
		if ready:
			set_freq_latch.next  	= set_freq
			set_step_f_latch.next	= set_step_f
			set_step_t_latch.next	= set_step_t
			set_wait_latch.next  	= set_wait

	quitold = Signal(bool(0))
	start_holdingold = Signal(bool(0))
	@always_seq(clk.posedge,reset=reset)
	def quit_monitor():
		quitold.next = quit
		start_holdingold.next = start_holdingold

		if quitold == 0 and quit == 1:
			quit_turnedon.next = 1
		else:
			quit_turnedon.next = 0

		if start_holdingold == 0 and start_holding == 1:
			start_holding_turnedon.next = 1
		else:
			start_holding_turnedon.next = 0

	@always(state,clk,start,quit_turnedon,dec_clk_int,add_o_int,sub_o_int,start_holding_turnedon)
	def fsm():
		''' Our beloved finite state machine! For controlling the frequency stepping of the PTS.
		It drives m_dec, which is a special counter that has both a binary output, and hexadecimal
		output (which is what the PTS needs. It steps through the frequency schedule.'''
		if state == t_state.WAIT and start == 1:
			dec_clk.next                	= 0
			add_o.next                  	= 0
			sub_o.next                  	= 0
			frequency_controller_en.next	= False
			waiter_en.next              	= False 
			ready.next                  	= True
			state.next = t_state.REACH_DESIRED
		elif state == t_state.REACH_DESIRED and not quit_turnedon:
			dec_clk.next                	= dec_clk_int 
			add_o.next                  	= add_o_int
			sub_o.next                  	= sub_o_int
			frequency_controller_en.next	= True
			waiter_en.next              	= False
			ready.next                  	= False
		elif state == t_state.REACH_DESIRED and quit_turnedon:
			state.next = t_state.HOLD_FREQ
			#let frequency_controller do its thing
		# elif state == t_state.REACH_DESIRED_CHANGE_STEP:
		#	dec_clk.next                	= dec_clk_int
		#	add_o.next                  	= add_o_int
		#	sub_o.next                  	= sub_o_int
		#	frequency_controller_en.next	= True
		#	waiter_en.next              	= False
		#	ready.next                  	= False
		 	#let frequency_controller do its thing
		else: #state == t_state.HOLD_FREQ:
			if start_holding_turnedon:
				state.next = t_state.WAIT

			dec_clk.next                	= 0
			add_o.next                  	= 0
			sub_o.next                  	= 0
			frequency_controller_en.next	= False
			waiter_en.next              	= True
			ready.next                  	= False

	#enabled/disabled versions of clk
	freq_controller_clk	= Signal(bool(0))
	waiter_clk         	= Signal(bool(0))
	dec_clk_en         	= Signal(bool(0))

	@always_comb
	def wiring():
		freq_controller_clk.next	= frequency_controller_en and clk
		waiter_clk.next         	= waiter_en	and clk
		dec_clk_int.next        	= dec_clk_en and clk
		curr_freq.next          	= bq

	delta_freq	= Signal(intbv(0,min = 0, max = 10**N))
	#step direction. move either up or down towards desired frequency
	d_state = enum('UP','DOWN')
	direction	= Signal(d_state.UP) #note that the initial state is UP, as the initial
	         	                  #frequency (curr_freq) is 0.

	@always_seq(freq_controller_clk.posedge,reset=reset)
	def frequency_controller():
		#transform from logarithm to number
		for power in range(0,N):
			if set_step_f_latch == power:
				delta_freq.next = 10**power

		#decide whether we add or subtract, or stop,
		#note that when it inevitably overshoots
		#the step goes down and compensates for it by 
		#switching direction.
		if curr_freq > set_freq_latch:
			quit.next = 0
			if direction == d_state.UP:
				if set_step_f_latch + set_step_f_latch_int >= 1:
					set_step_f_latch_int.next = set_step_f_latch_int - 1
				direction.next = d_state.DOWN
			else:
				direction.next = d_state.DOWN
		elif curr_freq < set_freq_latch + set_freq_latch_int:
			quit.next = 0
			if direction == d_state.DOWN:
				if set_step_f_latch + set_freq_latch_int >= 1:
					set_freq_latch_int.next = set_freq_latch_int - 1
				direction.next = d_state.UP
			else:
				direction.next = d_state.UP
		else:  #define the quit condition
			dec_clk_en.next	= 0
			incr_o.next    	= 0
			add_o_int.next 	= 0
			sub_o_int.next 	= 0
			quit.next      	= 1

		if direction == d_state.UP:
			# curr_freq.next	= curr_freq + delta_freq
			add_o_int.next = 1
			sub_o_int.next = 0
			incr_o.next    	= set_step_f_latch + set_freq_latch_int
			dec_clk_en.next	= 1
		else:
			# curr_freq.next	= curr_freq - delta_freq
			add_o_int.next = 0
			sub_o_int.next = 1
			incr_o.next    	= set_step_f_latch + set_freq_latch_int
			dec_clk_en.next	= 1

	#activates at HOLD_FREQ
	@always_seq(waiter_clk.posedge,reset=reset)
	def holder():
		if set_wait_latch + set_wait_latch_int == 0:
			start_holding.next = 1
		else:
			start_holding.next = 0
			set_wait_latch_int.next = set_wait_latch_int - 1
 
	return latcher, fsm, frequency_controller, holder, wiring, quit_monitor