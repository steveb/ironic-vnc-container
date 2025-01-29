FROM quay.io/centos/centos:stream9

RUN dnf -y install \
    epel-release && \
    dnf -y install \
    chromium \
    chromedriver \
    procps \
    python3-requests \
    python3-selenium \
    x11vnc \
    xorg-x11-server-Xvfb

ENV DISPLAY_WIDTH=1280
ENV DISPLAY_HEIGHT=960

ENV DRIVER='fake'

ADD bin/* /usr/local/bin
ADD drivers /drivers

ENTRYPOINT start-xvfb.sh