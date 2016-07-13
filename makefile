PYCC=pypy
CURDIR=$(shell pwd)

virtual_uart:
	cd ./run/; pwd; $(PYCC) -c 'import decisive_pony.virtual_uart'
	gtkwave  --cpu=4 run/test.vcd
	rm run/test.vcd

test_dec:
	cd ./run/; pwd; $(PYCC) -c 'import decisive_pony.testbench.tb_m_dec'
	gtkwave -o --cpu=4 run/testbench.vcd
sync:
	git push -u origin master

clean:
	rm *.vcd*