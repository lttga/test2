FROM python:3.7-alpine
ENV PYTHONDONTWRITEBYTECODE 1

ARG USER=spoonbill
RUN mkdir -p /data
WORKDIR /data
COPY . .

RUN apk update && apk add libpq sudo --no-cache && apk add --no-cache --virtual .build-deps gcc python3-dev musl-dev libffi-dev g++ gettext git findutils \
        && adduser -D $USER \
        && echo "$USER ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/$USER \
        && chmod 0440 /etc/sudoers.d/$USER \
        && python setup.py install \
        && find . -name \*.po -execdir sh -c 'msgfmt "$0" -o `basename $0 .po`.mo' '{}' \; \
        && apk del .build-deps gcc python3-dev musl-dev libffi-dev gettext git \
        && rm -fr /root/.cache
RUN chown -R $USER:$USER /data

USER spoonbill
CMD ["spoonbill"]
