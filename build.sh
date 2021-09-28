#!/usr/bin/env bash

cd "$(cd "$(dirname "$0")" >/dev/null 2>&1; pwd -P)" || exit 9

case "$1" in
  docker|container)
    DOCKER_IMAGE=pschmitt/zoom-calendar-events

    EXTRA_ARGS=()
    if [[ -n "$NO_CACHE" ]] || [[ "$2" == "--no-cache" ]]
    then
      EXTRA_ARGS+=(--no-cache)
    fi

    if docker build --pull -t "$DOCKER_IMAGE" "${EXTRA_ARGS[@]}" .
    then
      docker push "$DOCKER_IMAGE"
    fi
    ;;
  *)
    docker run -it --rm \
      -v "$PWD:/app" \
      -e STATICX=1 \
      -e CLEAN=1 \
      pschmitt/pyinstaller:3.9 zoom-calendar-events.py
    ;;
esac
