dtmc

const int N = 10;

module grid

	c : [0..N];
	g : [0..1];

	[] c < N & g = 0 ->   	(1/20): (c'=c) & (g'=g+1)
						+ (1-1/20): (c'=c+1) & (g'=g);
	[] c < N & g = 1 ->   	1: (c'=c+1) & (g'=g);

endmodule


label "bad" = g=1;

// The inductive invariant is exponential, but we should approximate it using pwaff stuff?
// Possible alternative: just do exponentials using z3 on value iteration instead?