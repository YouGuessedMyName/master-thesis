dtmc


const int maxx = 8;
const int to_send = 15;
const int package_size = 7;


module brp

	sent : [0..to_send] init 0;
	failed : [0..maxx] init 0;
	cur_package : [0..package_size] init 0;

	[] cur_package = package_size & sent < to_send -> 1 : (failed'=0)&(sent'=sent+1)&(cur_package'=0);

	
    [] cur_package < package_size & sent < to_send -> 
		1/5 : (failed'=failed+1)&(sent'=sent)&(cur_package'=cur_package)
		+ 4/5: (cur_package'=cur_package+1)&(sent'=sent)&(failed'=failed);

endmodule


label "goal" = failed=maxx;

