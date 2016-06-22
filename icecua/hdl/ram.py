from myhdl import *

@block
def ram(dout, din, addr, we, clk, depth=128):
    """  Ram model """

    mem = [Signal(intbv(0)[8:]) for i in range(depth)]

    @always(clk.posedge)
    def write():
        if we:
            mem[int(addr)].next = din

    @always_comb
    def read():
        dout.next = mem[int(addr)]

    return write, read
