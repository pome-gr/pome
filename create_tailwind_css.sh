#! /usr/bin/env bash
# export PURGE_CSS_ENABLED=true to enable purge
echo "Creating pome/static/tailwind.min.css"

if [ "$PURGE_CSS_ENABLED" == "true" ]; then echo "Purge CSS: enabled"; else echo "Purge CSS: not enabled (export PURGE_CSS_ENABLED=true to enable)"; fi

npx tailwindcss -o pome/static/tailwind.css && npx minify pome/static/tailwind.css > pome/static/tailwind.min.css && rm pome/static/tailwind.css

FILENAME=pome/static/tailwind.min.css
FILESIZE=$(wc -c < "$FILENAME")

echo "Size of $FILENAME = $FILESIZE bytes."