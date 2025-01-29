FROM mariadb:latest
ENV MYSQL_ROOT_PASSWORD=pass
ENV MYSQL_DATABASE=licenta
ENV MYSQL_USER=cosmin
ENV MYSQL_PASSWORD=cosmin

WORKDIR /bazadate
COPY user.sql /bazadate/user.sql

EXPOSE 3306