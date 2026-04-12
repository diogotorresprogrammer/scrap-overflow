#!/bin/bash
set -e

COMMAND="${1:-upgrade}"
ARG="${2:-head}"

cd "$(dirname "$0")/../backend"

case "$COMMAND" in
  upgrade)
    alembic upgrade "${ARG}"
    ;;
  downgrade)
    alembic downgrade "${ARG}"
    ;;
  revision)
    # Usage: ./migrate.sh revision "your message"
    alembic revision --autogenerate -m "${ARG}"
    ;;
  history)
    alembic history --verbose
    ;;
  current)
    alembic current
    ;;
  *)
    echo "Usage: $0 {upgrade|downgrade|revision|history|current} [arg]"
    exit 1
    ;;
esac
