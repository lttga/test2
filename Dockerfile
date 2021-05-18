FROM python:3.7-alpine
ENV PYTHONDONTWRITEBYTECODE 1
ENV UMASK 000

ARG USER=spoonbill
RUN mkdir -p /data /app
WORKDIR /app
COPY . .

RUN apk update && apk add libpq sudo --no-cache && apk add --no-cache --virtual .build-deps gcc python3-dev musl-dev libffi-dev g++ gettext git findutils \
        && apk add --no-cache bash \
        && adduser -D $USER \
        && echo "$USER ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/$USER \
        && chmod 0440 /etc/sudoers.d/$USER \
        && pip install Babel \
        && pip install . \
        && pybabel update -i spoonbill/locales/base.pot -D spoonbill -d spoonbill/locales/ \
        && pybabel compile -D spoonbill -d spoonbill/locales/ \
        && apk del .build-deps gcc python3-dev musl-dev libffi-dev gettext git \
        && rm -fr /root/.cache
RUN chown -R $USER:$USER /app /data
COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh
USER spoonbill
WORKDIR /data
ENTRYPOINT ["/entrypoint.sh"]
# CMD ["/usr/local/bin/spoonbill"]
