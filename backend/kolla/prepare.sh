#! /bin/bash

yum -y install epel-release
curl -sSL https://get.docker.io | bash
mkdir -p /etc/systemd/system/docker.service.d
config_path=/etc/systemd/system/docker.service.d/kolla.conf
daisy_config_file="/home/daisy_install/daisy.conf"
line=`sed '/^[[:space:]]*#/d' $daisy_config_file | sed /^[[:space:]]*$/d | grep -w "daisy_management_ip"| grep "daisy_management_ip[[:space:]]*=" -m1`
if [ -z "$line" ]; then
    echo "daisy_management_ip of daisy.conf can't be empty!"
    exit 1
else
    daisy_management_ip=`echo $line | sed 's/=/ /' | sed -e 's/^\w*\ *//'`
fi
touch /etc/sysconfig/docker
echo -e "other_args="--insecure-registry $daisy_management_ip:4000"" > /etc/sysconfig/docker
echo -e "[Service]\nMountFlags=shared\nEnvironmentFile=/etc/sysconfig/docker\nExecStart=\nExecStart=/usr/bin/docker daemon -H fd:// \$other_args" > $config_path
systemctl daemon-reload
systemctl restart docker
yum install -y python-docker-py
yum -y install ntp
systemctl enable ntpd.service
systemctl stop libvirtd.service
systemctl disable libvirtd.service
systemctl start ntpd.service
yum -y install ansible1.9