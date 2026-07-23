dtmc

const int N = 500000000000;

module grid

	c : [0..N] init 0;
	g : [0..1] init 0;

	[] c < N -> (1/1000000000000): (c'=c+1)&(g'=g+1) + 999999999999/1000000000000: (c'=c+1)&(g'=g);

endmodule


label "goal" = g=1;
