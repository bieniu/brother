ARG VARIANT="3.12"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

COPY requirements*.txt /tmp/pip-tmp/
RUN pip --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements-test.txt -r /tmp/pip-tmp/requirements.txt && rm -rf /tmp/pip-tmp

ENV SHELL /bin/bash
