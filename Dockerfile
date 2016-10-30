FROM gliderlabs/alpine
MAINTAINER Jaime Cochran <jcochran@cloudflare.com>
ADD telnetd /bin/telnetd
ADD dbus /bin/dbus
RUN echo "http://dl-cdn.alpinelinux.org/alpine/v3.4/community" | tee /etc/apk/repositories && \
  echo "http://dl-cdn.alpinelinux.org/alpine/v3.4/main" | tee -a /etc/apk/repositories && \
  apk update && \
  apk add --no-cache python && \
  apk add --no-cache py-pip && \
  pip install watchdog && \
  rm -f /etc/motd /etc/issue && \
  apk add --no-cache python && \
  chmod +x /bin/telnetd && \
  chmod +x /bin/dbus && \
  rm -f /etc/securetty
ADD run.sh /tmp/run.sh
RUN chmod +x /tmp/run.sh
EXPOSE 23
CMD ["sh", "/tmp/run.sh"]
