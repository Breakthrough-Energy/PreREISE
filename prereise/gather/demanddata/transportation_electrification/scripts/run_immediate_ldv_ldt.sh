#!/bin/bash 

nohup python -u generate_shape_cache_files.py ldv 100  </dev/null > nohup_ldv_100.out 2> nohup_ldv_100.err &

nohup python -u generate_shape_cache_files.py ldv 200  </dev/null > nohup_ldv_200.out 2> nohup_ldv_200.err &

nohup python -u generate_shape_cache_files.py ldv 300  </dev/null > nohup_ldv_300.out 2> nohup_ldv_300.err &

nohup python -u generate_shape_cache_files.py ldt 100  </dev/null > nohup_ldt_100.out 2> nohup_ldt_100.err &

nohup python -u generate_shape_cache_files.py ldt 200  </dev/null > nohup_ldt_200.out 2> nohup_ldt_200.err &

nohup python -u generate_shape_cache_files.py ldt 300  </dev/null > nohup_ldt_300.out 2> nohup_ldt_300.err &