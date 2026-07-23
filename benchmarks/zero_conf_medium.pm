dtmc

const int num_probes = 10000;

module zero_conf

	start : [0..1] init 1; // z
	established_ip: [0..1] init 0; // y
	cur_probe : [0..num_probes] init 0; // x

	[] start = 1 & established_ip = 0 -> 1/2: (start'=start-1)&(established_ip'=established_ip)&(cur_probe'=cur_probe) 
			+ 1/2 : (start'=start-1)&(established_ip'=established_ip+1)&(cur_probe'=cur_probe);

	[] start = 0 & established_ip = 0 & cur_probe < num_probes -> 999999999/1000000000: (start'=start)&(established_ip'=established_ip)&(cur_probe'=cur_probe + 1) 
			+ 1/1000000000:(start'=1)&(established_ip'=0)&(cur_probe'=0);

endmodule

label "goal" = established_ip=1;