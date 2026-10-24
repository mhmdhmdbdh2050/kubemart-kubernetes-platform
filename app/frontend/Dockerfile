FROM nginxinc/nginx-unprivileged:1.30.6-alpine3.24-perl

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html
COPY images/ /usr/share/nginx/html/images/

USER 101
EXPOSE 8080
