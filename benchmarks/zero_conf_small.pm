dtmc

const num_probes = 10;

module zero_conf

	start : bool init true; // z
	established_ip: bool init false; // y
	cur_probe : [0..num_probes] init 0; // x

	[] (start = true & established_ip = false) -> (0.5): (start'=false) + (0.5) : (start'=false)&(established_ip'=true);
	[] (start = false & established_ip = false & cur_probe < num_probes) -> (0.95):(cur_probe'=cur_probe + 1) + (1-0.95):(start'=true)&(cur_probe'=0);

endmodule

label "goal" = established_ip=true;

// When start gets true, there's a fifty percent chance of succeeding afterwards.
//The ind. inv. will look like chain again for all the states where start=false and 1/2 for all states where start=true. */

