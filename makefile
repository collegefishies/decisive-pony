PYCC=pypy
CURDIR=$(shell pwd)

tb_top.py:
	cd ./run/; pwd; $(PYCC) -c 'import decisive_pony.tb_top'
	gtkwave  --cpu=4 run/testbench.vcd

blinky: blinky.py
	pypy blinky.py
	yosys -p "synth_ice40 -blif blinky.blif" blinky.v
	arachne-pnr -d 8k -p ~/Documents/ybclock/decisive_pony/build/normal.pcf blinky.blif -o blinky.asc
	icepack blinky.asc blinky.bin
	sudo iceprog blinky.bin


top.py:
	cd ./run/; pwd; $(PYCC) -c 'import decisive_pony.top'
	cd ./run/; yosys -p "synth_ice40 -blif top.blif" top.v && arachne-pnr -d 8k -p ~/Documents/ybclock/decisive_pony/build/amphenol.pcf top.blif -o top.asc && icepack top.asc top.bin && sudo iceprog top.bin

virtual_uart.py:
	cd ./run/; pwd; $(PYCC) -c 'import decisive_pony.virtual_uart'
	gtkwave  --cpu=4 run/test.vcd
	rm run/test.vcd

with_uart.py:
	cd ./run/; pwd; $(PYCC) -c 'import decisive_pony.with_uart'
	gtkwave  --cpu=4 run/test.vcd
	# rm run/test.vcd

test_dec:
	cd ./run/; pwd; $(PYCC) -c 'import decisive_pony.testbench.tb_m_dec'
	gtkwave -o --cpu=4 run/testbench.vcd
sync:
	git push -u origin master

clean:
	rm *.vcd*