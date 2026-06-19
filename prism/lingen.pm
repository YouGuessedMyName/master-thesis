dtmc

const int X = 5;
const int Y = 2;

module grid
	x : [0..X];
	y : [0..Y];

    [] x = 0 & y = 0 -> (1/2) : (x'=1) & (y'=0)
                      + (1/2) : (x'=1) & (y'=2);
    [] 0 < x & x < X & y = 0 -> (9/10) : (x'=x+1) & (y'=y) + (1/10) : (x'=x) & (y'=y+1);
    [] 0 < x & x < X & y = 1 -> 1 : (x'=x+1) & (y'=y);
    [] 0 < x & x < X & y = 2 -> (9/10) : (x'=x+1) & (y'=y) + (1/10) : (x'=x) & (y'=y-1);
endmodule

label "bad" = y=1;