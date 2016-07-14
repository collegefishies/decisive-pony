module tb_top;

reg clk;
reg trigger;
reg fpga_rx;
reg fpga_tx;
wire [49:0] amphenol;

initial begin
    $from_myhdl(
        clk,
        trigger,
        fpga_rx,
        fpga_tx
    );
    $to_myhdl(
        amphenol
    );
end

top dut(
    clk,
    trigger,
    fpga_rx,
    fpga_tx,
    amphenol
);

endmodule
