#!/bin/bash 

nohup python -u generate_shape_cache_files.py mdv 200  </dev/null > nohup_mdv_200.out 2> nohup_mdv_200.err &

nohup python -u generate_shape_cache_files.py hdv 200  </dev/null > nohup_hdv_200.out 2> nohup_hdv_200.err &