#!/bin/bash

(
	sleep 4
	echo "started"
)&

/usr/bin/mgba $1 -g