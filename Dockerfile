# syntax=docker/dockerfile:1.7

# NOTE: Using Python 3.11 for MetaGPT compatibility
ARG BASE_IMAGE=nikolaik/python-nodejs:python3.11-nodejs22
ARG USERNAME=openhands
ARG UID=10001
ARG GID=10001
ARG PORT=8000

####################################################################################
# Builder (source mode)
# We copy source + build a venv here for local dev and debugging.
####################################################################################
FROM python:3.11-bullseye AS builder
ARG USERNAME UID GID
ENV UV_PROJECT_ENVIRONMENT=/agent-server/.venv
ENV UV_PYTHON_INSTALL_DIR=/agent-server/uv-managed-python

COPY --from=ghcr.io/astral-sh/uv /uv /uvx /bin/

RUN groupadd -g ${GID} ${USERNAME} \
 && useradd -m -u ${UID} -g ${GID} -s /usr/sbin/nologin ${USERNAME}
USER ${USERNAME}
WORKDIR /agent-server
# Cache-friendly: lockfiles first
COPY --chown=${USERNAME}:${USERNAME} openhands/openhands-agent-server/pyproject.toml openhands/README.md openhands/LICENSE ./
COPY --chown=${USERNAME}:${USERNAME} metagpt ./metagpt
COPY --chown=${USERNAME}:${USERNAME} openhands/openhands-sdk ./openhands-sdk
COPY --chown=${USERNAME}:${USERNAME} openhands/openhands-tools ./openhands-tools
COPY --chown=${USERNAME}:${USERNAME} openhands/openhands-workspace ./openhands-workspace
COPY --chown=${USERNAME}:${USERNAME} openhands/openhands-agent-server ./openhands-agent-server
RUN --mount=type=cache,target=/home/${USERNAME}/.cache,uid=${UID},gid=${GID} \
    uv python install 3.11 && uv venv --python 3.11 .venv && uv sync --no-editable --managed-python

####################################################################################
# Binary Builder (binary mode)
# We run pyinstaller here to produce openhands-agent-server
####################################################################################
FROM builder AS binary-builder
ARG USERNAME UID GID

# We need --dev for pyinstaller
RUN --mount=type=cache,target=/home/${USERNAME}/.cache,uid=${UID},gid=${GID} \
    uv sync --dev --no-editable

RUN --mount=type=cache,target=/home/${USERNAME}/.cache,uid=${UID},gid=${GID} \
    uv run pyinstaller openhands-agent-server/openhands/agent_server/agent-server.spec
# Fail fast if the expected binary is missing
RUN test -x /agent-server/dist/openhands-agent-server

####################################################################################
# Runtime (binary mode)
####################################################################################
FROM ${BASE_IMAGE} AS runtime
ARG USERNAME UID GID PORT

RUN groupadd -g ${GID} ${USERNAME} \
 && useradd -m -u ${UID} -g ${GID} -s /usr/sbin/nologin ${USERNAME} \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
 && rm -rf /var/lib/apt/lists/* \
 && chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}

USER ${USERNAME}
WORKDIR /app

COPY --from=binary-builder --chown=${USERNAME}:${USERNAME} /agent-server/dist/openhands-agent-server /app/openhands-agent-server
COPY --from=binary-builder --chown=${USERNAME}:${USERNAME} /agent-server/.venv /app/.venv

EXPOSE ${PORT}

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

ENTRYPOINT ["/app/openhands-agent-server"]