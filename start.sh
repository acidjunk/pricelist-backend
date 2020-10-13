#!/bin/bash
source venv/bin/activate
export $(cat env | grep -v ^# | xargs)
cd server
flask run -h 0.0.0.0
