#!/bin/bash
source venv/bin/activate
export $(cat env | grep -v ^# | xargs)
cd server
flask db migrate
echo "Don't forget to commit the migration, if any..."
