# MagnetDB api/worker image
#
# stages:
#   lncmi       : debian + LNCMI apt repository
#   magnettools : build the magnettools python wheel from the LNCMI debian source package
#   (final)     : runtime with system python3, libmagnettools1, magnettools wheel and uv
#
# the LNCMI repository public key is taken from the apt-depot project (named build context):
#   docker build --build-context apt-depot=../apt-depot -f Dockerfile .
# (docker compose: see additional_contexts in docker-compose-*.yml)
#
# security:
# - only lncmi-repo-ci-public-key.asc is read from apt-depot, its primary key fingerprint
#   is checked (LNCMI_KEY_FPR) and only that key is trusted, for the LNCMI repo only (signed-by)
# - the depot is read anonymously; if it ever requires credentials, provide an apt auth.conf
#   as a BuildKit secret (never as ARG/ENV/COPY, they would be stored in the image):
#     docker build --secret id=lncmi_apt_auth,src=$HOME/.config/lncmi/apt-auth.conf ...
#   it is only mounted during the RUN steps that access the depot

ARG DEBIAN_DIST=trixie
ARG MAGNETTOOLS_VERSION=1.2.1-1
ARG UV_VERSION=0.12.23

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# check and extract the LNCMI repo signing key (gpg stays in this throwaway stage)
FROM debian:${DEBIAN_DIST} AS lncmi-key
ARG LNCMI_KEY_FPR=BA8DB4F10380EAE7DAF06ED64814A19C535D3508
RUN apt-get update \
    && apt-get install -y --no-install-recommends gpg gpg-agent \
    && rm -rf /var/lib/apt/lists/*
COPY --from=apt-depot lncmi-repo-ci-public-key.asc /tmp/lncmi.asc
RUN export GNUPGHOME=$(mktemp -d) \
    && gpg --batch --quiet --import /tmp/lncmi.asc \
    && gpg --batch --with-colons --list-keys "${LNCMI_KEY_FPR}" | grep -q "^fpr:::::::::${LNCMI_KEY_FPR}:" \
    || { echo "ERROR: LNCMI repo key ${LNCMI_KEY_FPR} not found in apt-depot public key" >&2; exit 1; } \
    && gpg --batch --export --export-options export-minimal "${LNCMI_KEY_FPR}" > /lncmi.gpg \
    && gpgconf --kill all && rm -rf "$GNUPGHOME"

FROM debian:${DEBIAN_DIST} AS lncmi
ARG DEBIAN_DIST
ARG LNCMI_REPO=http://euler.lncmig.local/~christophe.trophime@LNCMIG.local/debian/
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 DEBIAN_FRONTEND=noninteractive
COPY --from=lncmi-key --chmod=644 /lncmi.gpg /etc/apt/keyrings/lncmi.gpg
RUN echo "deb [signed-by=/etc/apt/keyrings/lncmi.gpg] ${LNCMI_REPO} ${DEBIAN_DIST} main" \
        > /etc/apt/sources.list.d/lncmi.list \
    && echo "deb-src [signed-by=/etc/apt/keyrings/lncmi.gpg] ${LNCMI_REPO} ${DEBIAN_DIST} main" \
        >> /etc/apt/sources.list.d/lncmi.list

FROM lncmi AS magnettools
ARG MAGNETTOOLS_VERSION
RUN --mount=type=secret,id=lncmi_apt_auth,target=/etc/apt/auth.conf.d/lncmi.conf,required=false \
    apt-get update \
    && apt-get install -y --no-install-recommends \
        dpkg-dev build-essential cmake python3-dev pybind11-dev \
        libboost-filesystem-dev libboost-system-dev \
        libmagnettools-dev=${MAGNETTOOLS_VERSION}
COPY --from=uv /uv /usr/local/bin/
WORKDIR /src
# reproducible wheel (same hash as long as MAGNETTOOLS_VERSION is unchanged), see uv.lock
ENV SOURCE_DATE_EPOCH=0 UV_PYTHON=/usr/bin/python3 UV_PYTHON_DOWNLOADS=never
RUN --mount=type=secret,id=lncmi_apt_auth,target=/etc/apt/auth.conf.d/lncmi.conf,required=false \
    apt-get source magnettools=${MAGNETTOOLS_VERSION} \
    && cmake -S magnettools-*/Python -B build \
    && uv build --wheel --out-dir /wheels build \
    && ls -l /wheels

FROM lncmi
ARG MAGNETTOOLS_VERSION
ARG USERNAME=feelpp
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN --mount=type=secret,id=lncmi_apt_auth,target=/etc/apt/auth.conf.d/lncmi.conf,required=false \
    apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 libmagnettools1=${MAGNETTOOLS_VERSION} \
        ca-certificates curl git openssh-client sudo \
        iputils-ping vim-nox emacs-nox wait-for-it debconf-utils libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# local user matching the host user id and group id (-l: no lastlog entry, large uids)
RUN if ! getent group ${USER_GID} >/dev/null; then groupadd -g ${USER_GID} ${USERNAME}; fi \
    && useradd -l -m -s /bin/bash -u ${USER_UID} -g ${USER_GID} -G sudo,video ${USERNAME} \
    && echo "${USERNAME} ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} \
    && chmod 0440 /etc/sudoers.d/${USERNAME} \
    && mkdir -p /home/${USERNAME}/.ssh /home/${USERNAME}/.cache \
    && ssh-keyscan github.com >> /home/${USERNAME}/.ssh/known_hosts \
    && chown -R ${USER_UID}:${USER_GID} /home/${USERNAME}

ENV LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu/MagnetTools/:${LD_LIBRARY_PATH:-}"

# magnettools wheel, used as a flat index in pyproject.toml
COPY --from=magnettools /wheels/ /opt/wheels/

# uv replaces poetry to install python dependencies
COPY --from=uv /uv /uvx /usr/local/bin/
# - venv lives outside the bind-mounted sources (keep host .venv untouched)
# - copy mode since uv cache (volume) and venv are on different filesystems
# - only use system python3 (magnettools wheel is built for it)
ENV UV_PROJECT_ENVIRONMENT=/home/${USERNAME}/.venv \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=/usr/bin/python3

USER $USERNAME
WORKDIR /home/$USERNAME
