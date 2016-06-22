from myhdl import *

@block
def pll(clk_in,clk_out):
	clk_out.driven = True
	@always(clk_in)
	def wiring():
		pass

	return wiring



pll.verilog_code='''
// Thanks to Clifford Wolf for his explanation on PLL usage (https://github.com/cliffordwolf/yosys/issues/107#issuecomment-162163626)

// module pll(
//     input   $clk_in,// set_io $clk_in 21 
//     output  $clk_out     // set_io LED 99
// );

    wire $clk_in;

    wire $clk_out;
    wire BYPASS;
    wire RESETB;

    SB_PLL40_CORE #(
        .FEEDBACK_PATH("SIMPLE"),
        .PLLOUT_SELECT("GENCLK"),
        .DIVR(4'b0000),
        .DIVF(7'b1010010), 
        .DIVQ(3'b010),
        .FILTER_RANGE(3'b001),
    ) uut (
        .REFERENCECLK   ($clk_in),
        .PLLOUTGLOBAL   ($clk_out), 
        .BYPASS         (1'b0),
        .RESETB         (1'b1)
        //.LOCK (LOCK )
    );

    assign BYPASS = 0;
    assign RESETB = 1;
// endmodule
'''


