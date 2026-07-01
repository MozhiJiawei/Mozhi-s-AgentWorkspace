#!/bin/sh
set -eu

SOURCE_DIR="${DOCS_SOURCE:-/workspace}"
WORK_DIR="${DOCS_WORKDIR:-/tmp/mozhi-agent-workspace}"
OUTPUT_DIR="${DOCS_OUTPUT:-/site}"

if [ ! -d "$SOURCE_DIR" ]; then
  echo "docs source directory does not exist: $SOURCE_DIR" >&2
  exit 1
fi

if [ -z "$OUTPUT_DIR" ] || [ "$OUTPUT_DIR" = "/" ]; then
  echo "refusing to clear unsafe docs output directory: $OUTPUT_DIR" >&2
  exit 1
fi

rm -rf "$WORK_DIR" "$OUTPUT_DIR"
mkdir -p "$WORK_DIR" "$OUTPUT_DIR"

rsync -a --delete \
  --exclude ".git/" \
  --exclude ".tmp/" \
  --exclude "node_modules/" \
  --exclude "docs/.vitepress/cache/" \
  --exclude "docs/.vitepress/dist/" \
  --exclude "skills/**/.git/" \
  --exclude "skills/**/__pycache__/" \
  "$SOURCE_DIR"/ "$WORK_DIR"/

cd "$WORK_DIR"
python3 scripts/sync_skill_docs.py
/app/node_modules/.bin/vitepress build docs --outDir "$OUTPUT_DIR"
python3 scripts/write_docs_publish_state.py --output "$OUTPUT_DIR/material-quality/publish-state.json"

exec nginx -g "daemon off;"
