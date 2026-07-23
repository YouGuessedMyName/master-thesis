dtmc

const int N = 10000;
const int M = 10000;

module grid

	a : [0..N] init 0;
	b : [0..M] init 0;
	
	[] a < N & b < M -> 5/10: (a'=a+1)&(b'=b) + 5/10 : (a'=a)&(b'=b+1);

endmodule


label "goal" = b=M&a<N;

