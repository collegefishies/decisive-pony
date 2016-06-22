from myhdl import *

@block
def m_dec(clk, add,sub, q,incr=0,reset=None,N=10):
	#whether or not we need to subtract/add a certain digit
	to_subtract      	= [Signal(bool(0)) for i in range(N)]
	# to_subtract_sig	= ConcatSignal(*to_subtract)
	to_add           	= [Signal(bool(0)) for i in range(N)]
	# to_add_sig     	= ConcatSignal(*to_add)
	#decomposition of the binary number we're working with
	q_int_l = [Signal( intbv(0,min=0,max=10) ) for i in downrange(N)]
	q_int	= ConcatSignal(*reversed(q_int_l))

	@always(q_int,*q_int_l)
	def wiring():
		q.next = q_int

	@always(q_int,*to_add)
	def addlogic():
		to_add[0].next = 1
		for digit in range(1,N):
			to_add[digit].next = (q_int_l[digit-1] == 9) and to_add[digit-1]

	@always(q_int,*to_subtract)
	def sublogic():
		to_subtract[0].next = 1
		for digit in range(1,N):
			to_subtract[digit].next = (q_int_l[digit-1] == 0) and to_subtract[digit-1]

	@always_seq(clk.posedge, reset=reset)
	def counter():
		if reset:
			for digit in range(N):
				q_int_l[digit].next = 0
		else:
			if add == True and (not sub):
				#main stuff
				for digit in range(incr+1,N):
					if to_add[digit]:
						if q_int_l[digit] != 9:
							q_int_l[digit].next = q_int_l[digit] + 1
						else:
							q_int_l[digit].next = 0
					else:
						q_int_l[digit].next = q_int_l[digit]
				#edge case
				if q_int_l[incr] != 9:
					q_int_l[incr].next = q_int_l[incr] + 1
				else:
					q_int_l[incr].next = 0
			elif sub == True and (not add):
				#main stuff
				for digit in range(incr+1,N):
					if to_subtract[digit]:
						if q_int_l[digit] != 0:
							q_int_l[digit].next = q_int_l[digit] - 1
						else:
							q_int_l[digit].next = 9
					else:
						q_int_l[digit].next = q_int_l[digit]
				#edge case
				if q_int_l[incr] != 0:
					q_int_l[incr].next = q_int_l[incr] - 1
				else:
					q_int_l[incr].next = 9
			else:
				for digit in range(N):
					q_int_l[digit].next = q_int_l[digit]

	return wiring,counter,addlogic,sublogic