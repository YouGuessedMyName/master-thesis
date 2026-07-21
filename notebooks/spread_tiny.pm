dtmc

module spread

	x : [0..2];
    y : [0..4] init 2;

    [] x = 0 ->   	1/2: (x'=x+1) & (y'=y-1) + 1/2: (x'=x+1) & (y'=y+1);
    [] x = 1 & 0 < y ->   	1/2: (x'=x+1) & (y'=y-1) + 1/2: (x'=x+1) & (y'=y);
endmodule

label "bad" = x=2;