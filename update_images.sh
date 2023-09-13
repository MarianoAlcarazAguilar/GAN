#! /bin/bash

CATEGORY=$1
TOTAL_ITERATIONS=$2

python selenium_controler.py $CATEGORY $TOTAL_ITERATIONS
python cleaning_html.py $CATEGORY
python download_images.py $CATEGORY