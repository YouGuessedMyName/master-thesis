dtmc


const int maxx = 8;
const int to_send = 15;
const int package_size = 7;


module brp

	sent : [0..to_send] init 0;
	failed : [0..maxx] init 0;
	cur_package : [0..package_size] init 0;

	[] cur_package = package_size & sent = 0 -> 1 : (failed'=0)&(sent'=1)&(cur_package'=0);
	[] cur_package = package_size & sent = 1 -> 1 : (failed'=0)&(sent'=2)&(cur_package'=0);
	[] cur_package = package_size & sent = 2 -> 1 : (failed'=0)&(sent'=3)&(cur_package'=0);
	[] cur_package = package_size & sent = 3 -> 1 : (failed'=0)&(sent'=4)&(cur_package'=0);
	[] cur_package = package_size & sent = 4 -> 1 : (failed'=0)&(sent'=5)&(cur_package'=0);
	[] cur_package = package_size & sent = 5 -> 1 : (failed'=0)&(sent'=6)&(cur_package'=0);
	[] cur_package = package_size & sent = 6 -> 1 : (failed'=0)&(sent'=7)&(cur_package'=0);
	[] cur_package = package_size & sent = 7 -> 1 : (failed'=0)&(sent'=8)&(cur_package'=0);
	[] cur_package = package_size & sent = 8 -> 1 : (failed'=0)&(sent'=9)&(cur_package'=0);
	[] cur_package = package_size & sent = 9 -> 1 : (failed'=0)&(sent'=10)&(cur_package'=0);
	[] cur_package = package_size & sent = 10 -> 1 : (failed'=0)&(sent'=11)&(cur_package'=0);
	[] cur_package = package_size & sent = 11 -> 1 : (failed'=0)&(sent'=12)&(cur_package'=0);
	[] cur_package = package_size & sent = 12 -> 1 : (failed'=0)&(sent'=13)&(cur_package'=0);
	[] cur_package = package_size & sent = 13 -> 1 : (failed'=0)&(sent'=14)&(cur_package'=0);
	[] cur_package = package_size & sent = 14 -> 1 : (failed'=0)&(sent'=15)&(cur_package'=0);

    [] cur_package < package_size & sent < to_send -> 
		1/5 : (failed'=failed+1)&(sent'=sent)&(cur_package'=cur_package)
		+ 4/5: (cur_package'=cur_package+1)&(sent'=sent)&(failed'=failed);

endmodule


label "goal" = failed=maxx;

