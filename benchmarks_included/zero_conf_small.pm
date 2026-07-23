dtmc

const int num_probes = 10;

module zero_conf

	start : [0..1] init 1; // z
	established_ip: [0..1] init 0; // y
	cur_probe : [0..num_probes] init 0; // x

	[] start = 1 & established_ip = 0 -> 1/2: (start'=start-1)&(established_ip'=established_ip)&(cur_probe'=cur_probe) 
			+ 1/2 : (start'=start-1)&(established_ip'=established_ip+1)&(cur_probe'=cur_probe);

	[] start = 0 & established_ip = 0 & cur_probe < num_probes -> 95/100: (start'=start)&(established_ip'=established_ip)&(cur_probe'=cur_probe + 1) 
			+ 5/100:(start'=1)&(established_ip'=0)&(cur_probe'=0);

endmodule

label "goal" = established_ip=1;

// When start gets 1, there's a fifty percent chance of succeeding afterwards.
//The ind. inv. will look like chain again for all the states where start=0 and 1/2 for all states where start=1. */

