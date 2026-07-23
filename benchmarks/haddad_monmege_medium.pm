dtmc

const int N=5000;

module main
    start : [0..1] init 1;
    side : [0..1] init 0;
	x : [0..N] init 0;

	[] start = 1 & side = 0 -> 7/10 : (start'=start-1)&(side'=side)&(x'=x) + 3/10 : (start'=start-1)&(side'=side+1)&(x'=x);
	[] start = 1 & side = 1 -> 7/10 : (start'=start-1)&(side'=side-1)&(x'=x) + 3/10 : (start'=start-1)&(side'=side)&(x'=x);

	[] start = 0 & side = 0 & x < N -> 499/1000 : (start'=start)&(side'=side)&(x'=x+1) 
		+ 501/1000 : (start'=1)&(side'=0)&(x'=0);
	
	[] start = 0 & side = 1 & x < N -> 1/2 : (start'=start)&(side'=side)&(x'=x+1) 
		+ 1/2 : (start'=1)&(side'=0)&(x'=0);


endmodule

label "goal" = x=N & side=0;

