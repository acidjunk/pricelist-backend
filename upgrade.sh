#!/bin/bash
source venv/bin/activate
export $(cat env | grep -v ^# | xargs)
cd server
flask db upgrade
