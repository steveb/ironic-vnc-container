#!/bin/bash

set -eux

# start-selenium-browser.py &
x11vnc -nevershared -forever -afteraccept 'start-selenium-browser.py &' -gone 'killall -s SIGTERM python3'