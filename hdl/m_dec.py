from myhdl import *
from icecua.hdl import rom
@block
def m_dec(clk, add,sub, q, bq, incr=Signal(intbv(0,min=0,max=10)),reset=ResetSignal(0,active=1,async=True),N=10):
	''' A counter module with two outputs, q, bq, each being 
	the 'decimal' in hexadecimal representation, and the other being
	the binary representation. incr is the module that determines by
	what power of ten to increment by, i.e., q.next = q + 10**incr.
	add, and sub are clock enables that determine whether we should add
	or subtract.
	'''

	#whether or not we need to subtract/add a certain digit
	to_subtract      	= [Signal(bool(0)) for i in range(N)]
	# to_subtract_sig	= ConcatSignal(*to_subtract)
	to_add           	= [Signal(bool(0)) for i in range(N)]
	# to_add_sig     	= ConcatSignal(*to_add)
	#decomposition of the binary number we're working with
	q_int_l = [Signal( intbv(0,min=0,max=10) ) for i in downrange(N)]
	q_int	= ConcatSignal(*reversed(q_int_l))
	bq_int = Signal(intbv(0,min=-10**N,max=10**N))

	increment_amounts = tuple([10**i for i in range(N)])


	@always_seq(clk.posedge,reset=None)
	def wiring():
		q.next = q_int
		bq.next = bq_int

	@always(incr,q_int,*to_add)
	def addlogic():
		''' This module determines whether or not to add certain bits,
		in the case of carry over. First we make sure we don't add all
		the bits lower than increment, then we set the increment bit to add,
		and lastly we perform the logic neccessary to determine if bits greater
		than incr need to be added

		It's sensitivity list is long, this is neccessary as to allow the logic 
		to update to_add when any part of to_add changes, as is the case
		when performing carry logic.
		'''
		for digit in range(N):
			if digit < incr:
				to_add[digit].next = 0
			elif digit == incr:
				to_add[incr].next = 1
			else:
				to_add[digit].next = (q_int_l[digit-1] == 9) and to_add[digit-1]

	@always(incr,q_int,*to_subtract)
	def sublogic():
		''' This module determines whether or not to subtract certain bits,
		in the case of carry over. First we make sure we don't subtract all
		the bits lower than increment, then we set the increment bit to subtract,
		and lastly we perform the logic neccessary to determine if bits greater
		than incr need to be subtracted.

		It's sensitivity list is long, this is neccessary as to allow the logic 
		to update to_subtract when any part of to_subtract changes, as is the case
		when performing carry logic.
		'''
		for digit in range(N):
			if digit < incr:
				to_subtract[digit].next = 0
			elif digit == incr:
				to_subtract[incr].next = 1
			else:
				to_subtract[digit].next = (q_int_l[digit-1] == 0) and to_subtract[digit-1]

	@always_seq(clk.negedge, reset=reset)
	def hex_counter():
		''' This is the HEXADECIMAL counter.
		It adds or subtracts only if (add xor sub) is True, to allow for the carry logic
		a new bit of logic is required, namely addlogic, and sublogic. They give out 
		lists of vectors (or integer masks). These are used in the logic below. And work 
		out most of the stuff. One extra if statement is needed to increment the desired 
		byte.
		'''
		if add == True and (not sub):
			#work on the hexadecimal
			#main stuff
			for digit in range(1,N):
				if digit > incr:

					if to_add[digit]:
						if q_int_l[digit] != 9:
							q_int_l[digit].next = q_int_l[digit] + 1
						else:
							q_int_l[digit].next = 0
					else:
						q_int_l[digit].next = q_int_l[digit]
				elif digit == incr:
					#edge case
					if q_int_l[incr] != 9:
						q_int_l[incr].next = q_int_l[incr] + 1
					else:
						q_int_l[incr].next = 0
		elif sub == True and (not add):
			#main stuff
			for digit in range(1,N):
				if digit > incr:
					if to_subtract[digit]:
						if q_int_l[digit] != 0:
							q_int_l[digit].next = q_int_l[digit] - 1
						else:
							q_int_l[digit].next = 9
					else:
						q_int_l[digit].next = q_int_l[digit]
				elif digit == incr:
					#edge case
					if q_int_l[incr] != 0:
						q_int_l[incr].next = q_int_l[incr] - 1
					else:
						q_int_l[incr].next = 9
		else:
			for digit in range(N):
				q_int_l[digit].next = q_int_l[digit]

	# @block
	# def increment_amounts_rom():
	#	''' Here's where we define the rom '''


	#	return rom_inst

	increment = Signal(intbv(0,min=0,max=10**N + 1))

	rom_inst = rom(dout=increment,addr=incr,CONTENT=increment_amounts)


	@always_seq(clk.negedge,reset=reset)
	def bin_counter():
		''' Here is the binary counter for bq. 
		It's value should synchronously be the same
		as q. This logic should be simple, and it is,
		but it freaks out when you subtract too far. Be warned!'''

		if add and (not sub):
			bq_int.next = bq_int + increment
		elif sub and (not add):
			bq_int.next = bq_int - increment
		else:
			bq_int.next = bq_int


	return wiring,hex_counter,addlogic,sublogic,bin_counter,rom_inst