dtmc

const int N = 100;
const int M = 100;

module grid

	a : [0..N] init 0;
	b : [0..M] init 0;

	[] a < N & b < M -> 55/100: (a'=a+1)&(b'=b) + 45/100 : (a'=a)&(b'=b+1);

endmodule


label "goal" = b=M&a<N;

