FROM ubuntu:16.04
MAINTAINER b1ind

ENV DEBIAN_FRONTEND noninteractive

COPY app /qwb/app
COPY flag.txt /flag_qwb/flag
COPY start.sh /root/start.sh
COPY qwb.sql /tmp/qwb.sql
COPY sources.list /etc/apt/sources.list

RUN apt-get update \
    && apt-get install -y python3-pip mysql-server \
    && usermod -s /bin/bash mysql

RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple -U tornado==6.0.3 \
    && pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple -U pymysql==0.10.1 \
    && chmod 777 /qwb/app/*.html\
    && usermod -d /var/lib/mysql/ mysql\
    && ln -s /var/lib/mysql/mysql.sock /tmp/mysql.sock\
    && chown -R mysql:mysql /var/lib/mysql\
    && service mysql start\
    && chown -R mysql:mysql /var/run/mysqld\
    && mysql -uroot -e "create user qwb identified by 'qwb123456';"\
    && mysql -uroot -e "source /tmp/qwb.sql;"\
    && mysql -uroot -e "grant all on *.* to qwb@'%' identified by 'qwb123456' with grant option;"\
    && mysql -uroot -e "flush privileges;"\
    && chmod 777 /qwb/app\
    && sed -i 's/\r//' /root/start.sh

WORKDIR /qwb/app

ENTRYPOINT ["/bin/bash","/root/start.sh"]