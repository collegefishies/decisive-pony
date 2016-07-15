# decisive-pony

Repo for the PTS-FPGA controller of the Yb Clock of Vladan Vuletic's group.

#toolchain
contains the tools used to be build the current version of decisive-pony

#tex 
is documentation

#experimental
is test HDL.

#hdl
is final product HDL.

#run
holds simulation files.

#bin
has useful executables

# Using this thing

The top module is with_uart.py, this contains everything that's needed to
program the FPGA, just hook up the appropriate pins as given in build/

with_uart.py basically works by connecting a UART module (icecua.hdl.uart) with a couple rams (icecua.hdl.bussedram) and an arbiter (written in with_uart). Our program has already been shown to work if given a set of ROMs with the schedule programmed in (this is in virtual_uart.py). virtual_uart and with_uart are similiar in that they both contain m_manager, m_dec, pts_controller connected together (hardware blocks belonging to decisive_pony.hdl). 

pts_controller connects a hex_freq (output from m_dec) to the amphenol pins (permuted as necessary). Amphenol driving has been shown to work. However its uncertain as to what the ones digit is so whatever is put into hex_freq is mapped to 10\times what it should be. 