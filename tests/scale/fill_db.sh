#!/bin/sh -ex

./setup.py
for i in 0 1 2 3 4 5 6 7; do
	./add_rack.py --building np --rack $i --subnet $i --aqservice $USER &
done

wait
echo "Take a snapshot of the db..."

