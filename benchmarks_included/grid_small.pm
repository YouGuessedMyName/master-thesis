dtmc

const int N = 32;
const int M = 32;

module grid

	a : [0..N] init 0;
	b : [0..M] init 0;

	[] a < N & b < M -> 7/10: (a'=a+1)&(b'=b) + 3/10 : (a'=a)&(b'=b+1);

endmodule


label "goal" = b=M&a<N;

