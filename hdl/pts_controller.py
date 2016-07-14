from myhdl import *
from icecua.hdl import *

@block
def pts_controller(hex_freq,pts_enable, amphenol):
	amphenol_l = [Signal(False) for i in range(50)]
	amphenol_int = ConcatSignal(*reversed(amphenol_l))
	@always_comb
	def wiring():
		amphenol.next = amphenol_int
		#connect our grounds
		amphenol_l[49].next = 0  #nc -- wired to ground

		#testled to NC
		amphenol_l[48].next = 1
		# amphenol_l[44].next = clk


		#connect our signals
		#make sure the latch enable is true
		amphenol_l[41].next = not pts_enable #remote enable
		#disable? signal voltage setting
		amphenol_l[20].next = 0 #ground
		amphenol_l[21].next = 0	##nc
		#latches must be left high (false)
		amphenol_l[22].next = 1	#latch enable
		amphenol_l[23].next = 1	#latch enable
		amphenol_l[24].next = 1	#latch enable
		amphenol_l[45].next = 1	#latch enable
		amphenol_l[46].next = 1	#latch enable
		#hexadecimal
		amphenol_l[43].next	= not hex_freq[33]
		amphenol_l[42].next	= not hex_freq[32]
		amphenol_l[40].next	= not hex_freq[31]
		amphenol_l[39].next	= not hex_freq[30]
		amphenol_l[15].next	= not hex_freq[29]
		amphenol_l[14].next	= not hex_freq[28]
		amphenol_l[19].next	= not hex_freq[27]
		amphenol_l[18].next	= not hex_freq[26]
		amphenol_l[17].next	= not hex_freq[25]
		amphenol_l[16].next	= not hex_freq[24]
		amphenol_l[26].next	= not hex_freq[23]
		amphenol_l[25].next	= not hex_freq[22]
		amphenol_l[1].next 	= not hex_freq[21]
		amphenol_l[0].next 	= not hex_freq[20]
		amphenol_l[28].next	= not hex_freq[19]
		amphenol_l[27].next	= not hex_freq[18]
		amphenol_l[3].next 	= not hex_freq[17]
		amphenol_l[2].next 	= not hex_freq[16]
		amphenol_l[30].next	= not hex_freq[15]
		amphenol_l[29].next	= not hex_freq[14]
		amphenol_l[5].next 	= not hex_freq[13]
		amphenol_l[4].next 	= not hex_freq[12]
		amphenol_l[32].next	= not hex_freq[11]
		amphenol_l[31].next	= not hex_freq[10]
		amphenol_l[7].next 	= not hex_freq[9]
		amphenol_l[6].next 	= not hex_freq[8]
		amphenol_l[34].next	= not hex_freq[7]
		amphenol_l[33].next	= not hex_freq[6]
		amphenol_l[9].next 	= not hex_freq[5]
		amphenol_l[8].next 	= not hex_freq[4]
		amphenol_l[36].next	= not hex_freq[3]
		amphenol_l[35].next	= not hex_freq[2]
		amphenol_l[11].next	= not hex_freq[1]
		amphenol_l[10].next	= not hex_freq[0]
		amphenol_l[38].next	= 0 #not hex_freq[-1]  #SETS CHANNEL PORT
		amphenol_l[37].next	= 1 #not hex_freq[-2]	#unknown probably tens or ones digit  
		amphenol_l[13].next	= 1 #not hex_freq[-3]	#unknown probably tens or ones digit
		amphenol_l[12].next	= 1 #not hex_freq[-4]	#unknown probably tens or ones digit

	return wiring