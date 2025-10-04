FROM python:3.12-bookworm AS builder


COPY pyproject.toml ./pyproject.toml

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

RUN /root/.local/bin/uv pip install -r ./pyproject.toml --system

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
