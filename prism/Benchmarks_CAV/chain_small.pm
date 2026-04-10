dtmc

const M = 1;
const N= 5*M;

module grid

	c : [0..N] init 0;
	g : bool init false;

	[] (c < N) -> (0.05): (g'=true) + 0.95: (c'=c+1);

endmodule


label "goal" = g=true;

// The inductive invariant is exponential, but we should approximate it using pwaff stuff?
// Possible alternative: just do exponentials using z3 on value iteration instead?