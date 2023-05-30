#!/usr/bin/env bash
set -eu

pip-compile requirements.in --resolver=backtracking "$@"
pip-compile requirements-dev.in --resolver=backtracking "$@"
