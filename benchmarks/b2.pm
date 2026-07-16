// 0.8
dtmc

const int N = 5;

module grid

	c : [0..N-1];
	g : [0..1];

	[] c < N & g = 0 ->   	(1/10): (c'=c+1) & (g'=g+1)
						+ (1-1/10): (c'=c+1) & (g'=g);
	[] c < N & g = 1 ->   	1: (c'=c+1) & (g'=g);

endmodule


label "bad" = g=1;