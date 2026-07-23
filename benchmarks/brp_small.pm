dtmc


const int maxx = 8;
const int to_send = 15;
const int package_size = 7;


module brp

	sent : [0..to_send] init 0;
	failed : [0..maxx] init 0;
	cur_package : [0..package_size] init 0;

	[] cur_package = package_size & sent = 0 -> 1 : (sent'=1)&(failed'=0)&(cur_package'=0);
	[] cur_package = package_size & sent = 1 -> 1 : (sent'=2)&(failed'=0)&(cur_package'=0);
	[] cur_package = package_size & sent = 2 -> 1 : (sent'=3)&(failed'=0)&(cur_package'=0);
	[] cur_package = package_size & sent = 3 -> 1 : (sent'=4)&(failed'=0)&(cur_package'=0);
	[] cur_package = package_size & sent = 4 -> 1 : (sent'=5)&(failed'=0)&(cur_package'=0);
	[] cur_package = package_size & sent = 5 -> 1 : (sent'=6)&(failed'=0)&(cur_package'=0);
	[] cur_package = package_size & sent = 6 -> 1 : (sent'=7)&(failed'=0)&(cur_package'=0);
	[] cur_package = package_size & sent = 7 -> 1 : (sent'=8)&(failed'=0)&(cur_package'=0);
	[] cur_package = package_size & sent = 8 -> 1 : (sent'=9)&(failed'=0)&(cur_package'=0);
	[] cur_package = package_size & sent = 9 -> 1 : (sent'=10)&(failed'=0)&(cur_package'=0);
	[] cur_package = package_size & sent = 10 -> 1 : (sent'=11)&(failed'=0)&(cur_package'=0);
	[] cur_package = package_size & sent = 11 -> 1 : (sent'=12)&(failed'=0)&(cur_package'=0);
	[] cur_package = package_size & sent = 12 -> 1 : (sent'=13)&(failed'=0)&(cur_package'=0);
	[] cur_package = package_size & sent = 13 -> 1 : (sent'=14)&(failed'=0)&(cur_package'=0);
	[] cur_package = package_size & sent = 14 -> 1 : (sent'=15)&(failed'=0)&(cur_package'=0);

    [] cur_package < package_size & sent < to_send -> 
		1/5 : (sent'=sent)&(failed'=failed+1)&(cur_package'=cur_package)
		+ 4/5: (sent'=sent)&(failed'=failed)&(cur_package'=cur_package+1);

endmodule


label "goal" = failed=maxx;

