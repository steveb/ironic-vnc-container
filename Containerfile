FROM quay.io/centos/centos:stream9

RUN dnf -y install \
    epel-release && \
    dnf -y install \
    firefox \
    python3-requests \
    python3-selenium \
    x11vnc \
    xorg-x11-server-Xvfb

ENV GECKODRIVER='https://github.com/mozilla/geckodriver/releases/download/v0.35.0/geckodriver-v0.35.0-linux64.tar.gz'

RUN cd /usr/local/bin && \
    curl -L $GECKODRIVER | tar xz

ENV DISPLAY_WIDTH=1280
ENV DISPLAY_HEIGHT=960