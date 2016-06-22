PYCC=pypy
PYTHONPATH = $PYTHONPATH:$pwd


test_dec:
	$(PYCC) testbench/tb_m_dec.py


sync:
	cp ~/bin/backup bin/
	cp ~/bin/catfile bin/
	cp ~/bin/eqmplot bin/
	cp ~/bin/toice bin/
	cp ~/bin/vwrap bin/
	git add bin/*
	git add makefile
	git push -u origin master