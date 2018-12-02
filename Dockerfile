FROM python:3.5-slim

RUN apt-get update && \
apt-get -y upgrade && \
apt-get install -y gcc net-tools curl iputils-ping openssh-server jq tree

RUN mkdir /var/run/sshd && \
echo "root:root" | chpasswd && \
sed -ri 's/^PermitRootLogin\s+.*/PermitRootLogin yes/' /etc/ssh/sshd_config && \
sed -ri 's/UsePAM yes/#UsePAM yes/g' /etc/ssh/sshd_config && \
echo "alias ll='ls -la'" >> ~/.bashrc

RUN mkdir /opt/hailstorms \
/opt/hailstorms/running \
/opt/hailstorms/generated \
/opt/hailstorms/scripts \
/opt/hailstorms/helpscripts \
/opt/hailstorms/.ssh \
/opt/hailstorms/.aws

COPY framework/ /opt/hailstorms/framework/
RUN pip install -r /opt/hailstorms/framework/requirements.txt

COPY docs/ /opt/hailstorms/docs/
RUN touch /opt/hailstorms/helpscripts/__default__
# COPY helpscripts/ /opt/hailstorms/helpscripts/
COPY hailstorms/ /opt/hailstorms/hailstorms/

EXPOSE 22 8008 3456

ENTRYPOINT ["/opt/hailstorms/hailstorms/entrypoint"]

CMD []
