FROM python:3.12-bookworm AS builder

COPY Pipfile /tmp/Pipfile
COPY Pipfile.lock /tmp/Pipfile.lock

RUN python3 -m pip install pipenv \
  && PIPENV_PIPFILE=/tmp/Pipfile pipenv install \
  --system --ignore-pipfile --deploy

FROM python:3.12-slim-bookworm

COPY --from=builder /usr/local/lib/python3.12/site-packages \
  /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/lib/python3.12/lib-dynload \
  /usr/local/lib/python3.12/lib-dynload
COPY --from=builder /usr/local/bin /usr/local/bin

COPY app /app
RUN chown -R nobody:nogroup /app

ARG APP_VERSION='-'
ENV APP_VERSION=${APP_VERSION}
ARG BUILD_DATE='-'
ENV BUILD_DATE=${BUILD_DATE}

USER nobody
WORKDIR /app

CMD ["./main.py"]
