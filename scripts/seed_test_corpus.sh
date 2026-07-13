#!/usr/bin/env bash
# Seed a diverse local test corpus and index it into a Datashare project,
# for exercising `tarentula similar-docs` against realistic data:
#   - 20 Newsgroups (~14 MB, ~19k text files in 20 labeled topic folders):
#     labeled ground truth to judge a derived query's precision/recall.
#   - Govdocs1 (zips of 1000 mixed-format .gov files: PDF/DOC/XLS/PPT/HTML/...):
#     format and size diversity for the facet-narrowing steps.
#
# Requires: a running embedded Datashare (its ES on :9200) and the `datashare` CLI.
# Downloads are skipped when already extracted, so the script is re-runnable.
#
# Usage: scripts/seed_test_corpus.sh [num_govdocs_zips]   # default 2 (~600 MB)
#   DATA_DIR, PROJECT, ES_URL env vars override the defaults below.
set -euo pipefail

DATA_DIR="${DATA_DIR:-$HOME/datasets/test-corpus}"
PROJECT="${PROJECT:-test-corpus}"
ES_URL="${ES_URL:-http://localhost:9200}"
NUM_GOVDOCS_ZIPS="${1:-2}"

mkdir -p "$DATA_DIR"

if [ ! -d "$DATA_DIR/20news-bydate-train" ]; then
    echo ">> downloading 20 Newsgroups"
    curl -fL --retry 3 http://qwone.com/~jason/20Newsgroups/20news-bydate.tar.gz \
        | tar xz -C "$DATA_DIR"
fi

for i in $(seq 0 $((NUM_GOVDOCS_ZIPS - 1))); do
    zip=$(printf '%03d' "$i")
    dir="$DATA_DIR/govdocs1-$zip"
    if [ ! -d "$dir" ]; then
        echo ">> downloading govdocs1 $zip.zip"
        curl -fL --retry 3 -o "$DATA_DIR/$zip.zip" \
            "https://digitalcorpora.s3.amazonaws.com/corpora/files/govdocs1/zipfiles/$zip.zip"
        unzip -q "$DATA_DIR/$zip.zip" -d "$dir"
        rm "$DATA_DIR/$zip.zip"
    fi
done

echo ">> indexing $DATA_DIR into Datashare project '$PROJECT' (OCR off)"
datashare --mode CLI --stages SCAN,INDEX \
    --defaultProject "$PROJECT" \
    --dataDir "$DATA_DIR" \
    --elasticsearchAddress "$ES_URL" \
    --ocr false \
    --dataSourceUrl 'jdbc:sqlite:file:memorydb.db?mode=memory&cache=shared'

echo ">> done:"
curl -s "$ES_URL/$PROJECT/_count" && echo
