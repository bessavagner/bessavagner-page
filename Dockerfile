###
# PYTHON BUILD STAGE
###
FROM python:3.12.3-slim-bookworm as python_builder
LABEL stage=python_builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt requirements.txt

RUN python3 -m venv /usr/local/.venv && \
    /usr/local/.venv/bin/pip config set global.trusted-host "pypi.org files.pythonhosted.org pypi.python.org" &&\
    /usr/local/.venv/bin/pip install --upgrade pip && \
    /usr/local/.venv/bin/pip install --no-cache-dir -r requirements.txt && \
    /usr/local/.venv/bin/pip install --no-cache-dir pip-system-certs

# END BUILD STAGE
###

###
# FINAL STAGE
###
FROM python:3.12.3-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED 1
ENV ID_GROUP=1004
ENV ID_USER=1004
ENV GROUP=app
ENV USER=app-user
ENV USER_DIR=/usr
ENV SRC_DIR="$USER_DIR/src/"

RUN addgroup --gid ${ID_GROUP} ${GROUP} \
    && adduser --uid ${ID_USER} --gid ${ID_GROUP} --home "$USER_DIR/home/" --disabled-password ${USER} \
    && apt-get update

COPY ./ $SRC_DIR
COPY --from=python_builder /usr/local/.venv /usr/local/.venv

RUN chown -R ${ID_USER}:${ID_GROUP} "$SRC_DIR" \
    && chown -R ${ID_USER}:${ID_GROUP} "$USER_DIR/home/" \
    && chmod 755 "$SRC_DIR/entrypoint.sh"

ENV PATH="/usr/local/.venv/bin:$PATH"
USER $USER
EXPOSE 8081
WORKDIR $SRC_DIR

ENTRYPOINT ["./entrypoint.sh"]