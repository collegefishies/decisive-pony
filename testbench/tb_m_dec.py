from myhdl import *
from icecua.sim import clkdriver
from hdl import m_dec


@block
def testbench():
	N=9
	clk = Signal(bool(0))
	add = Signal(bool(0))
	sub = Signal(bool(0))
	incr = Signal(intbv(0,min=0,max=N))
	q = Signal(intbv(0)[4*N:])
	bq = Signal(intbv(0,min=-10**N-1, max=10**N + 1))

	reset = ResetSignal(0,active=1,async=False)
	modules = [clkdriver(clk)]
	modules.append(
			m_dec(clk=clk,add=add,sub=sub,q=q,bq=bq,incr=incr,reset=reset,N=N)
		)

	@instance
	def stimulus():
		yield delay(100)
		add.next = 1 
		incr.next = 1
		yield delay(200)
		incr.next = 4
		yield delay(400)
		incr.next = 3
		add.next = 0
		sub.next = 1
		pass
	return modules,stimulus

tb = testbench()
tb.convert()
tb.config_sim(trace=True)
tb.run_sim(20000)