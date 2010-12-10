#!/bin/sh
while read city timezone ; do
  echo aq update city --city $city --timezone $timezone
done </ms/dist/aurora/PROJ/data/incr/city2tz
