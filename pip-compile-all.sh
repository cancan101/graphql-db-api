#!/usr/bin/env bash
set -eu

pip-compile requirements.in "$@"
pip-compile requirements-dev.in "$@"
