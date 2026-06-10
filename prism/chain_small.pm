dtmc

// 1000000000000

const int N = 1000000000000;

module grid

	c : [0..N-1];
	g : [0..1];

	[] c < N & g = 0 ->   	(1/100000000000000): (c'=1) & (g'=g+1)
						+ (1-1/100000000000000): (c'=c+1) & (g'=g);
	[] c < N & g = 1 ->   	1: (c'=c+1) & (g'=g);

endmodule


label "bad" = g=1;

// The inductive invariant is exponential, but we should approximate it using pwaff stuff?
// Possible alternative: just do exponentials using z3 on value iteration instead?