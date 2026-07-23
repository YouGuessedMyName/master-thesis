dtmc

const int N=500000000;

module main
    start : [0..1] init 1;
    side : [0..1] init 0;
	x : [0..N] init 0;

	[] start = 1 & side = 0 -> 7/10 : (start'=start-1)&(side'=side)&(x'=x) + 3/10 : (start'=start-1)&(side'=side+1)&(x'=x);
	[] start = 1 & side = 1 -> 7/10 : (start'=start-1)&(side'=side-1)&(x'=x) + 3/10 : (start'=start-1)&(side'=side)&(x'=x);

	[] start = 0 & side = 0 & x < N -> 51/100 : (start'=start)&(side'=side)&(x'=x+1) 
		+ 49/100 : (start'=1)&(side'=0)&(x'=0);
	
	[] start = 0 & side = 1 & x < N -> 1/2 : (start'=start)&(side'=side)&(x'=x+1) 
		+ 1/2 : (start'=1)&(side'=0)&(x'=0);


endmodule

label "goal" = x=N & side=0;
