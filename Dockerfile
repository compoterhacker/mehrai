FROM gliderlabs/alpine
MAINTAINER Jaime Cochran <jcochran@cloudflare.com>
ADD telnetd /bin/telnetd
RUN echo "http://dl-cdn.alpinelinux.org/alpine/v3.4/community" | tee /etc/apk/repositories && \
  echo "http://dl-cdn.alpinelinux.org/alpine/v3.4/main" | tee -a /etc/apk/repositories && \
  apk update && \
  rm -f /etc/motd /etc/issue && \
  chmod +x /bin/telnetd && \
  rm -f /etc/securetty
EXPOSE 23
CMD telnetd -b 0.0.0.0:23; \
    /bin/sh
