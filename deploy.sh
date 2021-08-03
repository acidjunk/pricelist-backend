#!/bin/bash
/Users/acidjunk/miniconda3/bin/conda activate py37
source deploy/bin/activate
cd server
zappa update
