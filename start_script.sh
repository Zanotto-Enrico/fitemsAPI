#!/bin/bash

cd API;
flask run --host=0.0.0.0 --port=5001 &> ../log.txt
