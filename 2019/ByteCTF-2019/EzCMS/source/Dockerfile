FROM php:7.3-apache

LABEL Author="glzjin <i@zhaoj.in>" Blog="https://www.zhaoj.in"

COPY ./files /tmp/
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y zlib1g-dev libzip-dev && \
    cp -rf /tmp/html/ /var/www/ && \
    mkdir /var/www/html/sandbox && \
    chown -R root:root /var/www/html && \
    chmod -R 755 /var/www/html && \
    chown -R www-data:www-data /var/www/html/sandbox && \
    echo 'glzjin_wants_a_girl_firend' >> /var/www/html/sandbox/index.html && \
    docker-php-ext-install zip && \
    docker-php-ext-enable zip

CMD sh -c "echo $FLAG > /flag && export FLAG=not_flag && FLAG=not_flag && apache2-foreground"
