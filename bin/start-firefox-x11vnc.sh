#!/bin/bash

set -eux

# firefox ${FIREFOX_ARGS} -width ${DISPLAY_WIDTH} -height ${DISPLAY_HEIGHT} &

start-selenium-firefox.py &

x11vnc