dtmc

// 1000000000000

const int N = 1000;

module chain

	c : [0..N-1];
	g : [0..1];

	[] c < (N-1) & g = 0 ->   	(1/10): (c'=c+1) & (g'=g+1)
						+ (1-1/10): (c'=c+1) & (g'=g);
	[] c < N & g = 1 ->   	1: (c'=c+1) & (g'=g);

endmodule


label "bad" = g=1;

// The inductive invariant is exponential, but we should approximate it using pwaff stuff?
// Possible alternative: just do exponentials using z3 on value iteration instead?