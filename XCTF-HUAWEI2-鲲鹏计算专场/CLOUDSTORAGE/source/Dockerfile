FROM node:12
COPY ./files /usr/local/app
COPY ./env.txt /usr/local/app/.env
WORKDIR /usr/local/app
RUN npm i --registry=https://registry.npm.taobao.org
CMD node /usr/local/app/app.js
