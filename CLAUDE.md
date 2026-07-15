# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Rules

- Do not push code without human approval first.

## What this is

`tarentula` is a CLI toolbelt (and Python API) for bulk operations against a [Datashare](https://datashare.icij.org) instance and its backing Elasticsearch index. Commands count, download, export, tag, aggregate, and list metadata over documents matched by a query.

## Commands

Managed with Poetry. Tests require a **running Datashare + Elasticsearch** (they hit real HTTP endpoints, not mocks — except a few that use `responses`).

```bash
make install                      # poetry install --with dev
make test                         # poetry run pytest
poetry run pytest tests/test_count.py                 # single test file
poetry run pytest tests/test_count.py::TestCount::test_x  # single test
poetry run pylint tarentula       # lint (config in pylintrc)
make patch|minor|major            # bump version + git tag (see Makefile)
```

Point tests at your services with env vars: `TEST_ELASTICSEARCH_URL` (default `http://elasticsearch:9200`), `TEST_DATASHARE_URL` (default `http://localhost:8080`). Tests run against project `test-datashare`, created/torn down per class.

## Architecture

Three layers, and understanding the split matters before touching anything:

1. **`cli.py`** — the only Click surface. Each subcommand is a thin `@click.command` that collects options and delegates to a command class's `.start()`. Adding a command = write a class with `__init__(**options)` + `start()`, then a Click function that instantiates it and registers via `cli.add_command`. The `aggregate` command is the exception: it dispatches on `--run` to one of several classes (`aggregate.py`).

2. **Command classes** (`count.py`, `download.py`, `export_by_query.py`, `tagging.py`, `tagging_by_query.py`, `tag_cleaning_by_query.py`, `metadata_fields.py`, `aggregate.py`, `sim_docs.py`) — one class per operation. Each holds its options as attributes and drives the workflow in `start()`.

3. **`datashare_client.py`** — `DatashareClient` wraps all HTTP. Key detail: **it talks to Elasticsearch directly when `--elasticsearch-url` is set, otherwise routes ES searches through Datashare's proxy** (`/api/index/search/`) — see `elasticsearch_host`. This dual path is why most commands take both a `--datashare-url` and an optional `--elasticsearch-url`. `scan_all` (scroll API) vs `query_all` (`search_after`/`from`+`size` pagination, respects `limit`) are the two ways to page results; `scan_or_query_all` picks based on whether `--scroll` is set.

### Cross-cutting conventions

- **Query bodies**: a `--query` starting with `@` is read as a JSON file path; otherwise it's an ES `query_string` wrapped in a bool with a `type` match. This `@file`-vs-string logic is duplicated across `Command` (base in `command.py`), `sim_docs.py`, and `tag_cleaning_by_query.py` — keep them consistent if you change the query shape.
- **`cookies` / `headers`**: cookie-string parsing (`SimpleCookie`) and `Authorization: bearer <apikey>` header building are repeated per command class (not centralized beyond `DatashareClient`). Match the existing pattern rather than inventing a new one.
- **Config resolution**: `ConfigFileReader` is used as each option's Click `default` — it's a callable that reads `[DEFAULT]`/`[logger]` sections from the first found of `$TARENTULA_CONFIG`, `./tarentula.ini`, `~/.tarentula.ini`, `/etc/tarentula/tarentula.ini`. CLI flags override the file.
- **Tagging by query** uses ES `_update_by_query` with a Painless script and supports async tasks via `--wait-for-completion`.
- **Logging**: `logger.py` configures syslog + stdout handlers; `--progressbar` auto-enables only when `stdout_loglevel > INFO`.

### `sim_docs.py` (branch `feat_sim_docs`)

The `similar_docs` command is an **interactive** (uses `inquirer` prompts) session that: queries docs, lets the user narrow by facet aggregations, pick 2+, finds common lines/ngrams and salient terms between their content, builds an ES `more_like_this` query from the selection, and loops (facet-narrow → precision check → false-positive marking) until the user saves the resulting query to a JSON file. See `COOKBOOK_similar_docs.md` for the full walkthrough.

**Goal of this branch (`feat_sim_docs`) — work in progress, far from finished:**

Build a command that helps a user converge on a query retrieving *similar* documents. Target workflow:

1. Start from an initial query. Its results are typically heterogeneous (very different kinds of docs).
2. Interactively narrow the batch. The user can either hand-pick specific docs from the first results, **or** quickly filter by checking options the CLI prompts from **aggregations on the current results** — at minimum by file extension / content type, language, and file-size ranges. **Done**: `facet_aggregations`/`filter_by_facets` run before hand-picking and again after each `more_like_this` round.
3. On submit, use Elasticsearch features (e.g. `more_like_this`, term/aggregation analysis) to derive the query — or set of queries — that best captures what the user targeted: **maximize the targeted docs returned while minimizing false positives.** **Done**: `build_mlt_query` + salient-term (`significant_text`) suggestions + a precision proxy (how many seed docs still match) + false-positive marking that feeds `unlike` docs/terms into the next round.
4. Save the resulting query. **Done**.

Remaining: cookbook screenshot captures (`docs/captures/simdocs-0{1..4}...png`, tracked as a late TODO — the flow will still change). Query-builder functions are unit-tested (`tests/test_sim_docs_facets.py`); live-ES paths (`facet_aggregations`, `query_all`, `count_matches`) are covered in `tests/test_sim_docs_live.py`.

## Local dev testing (against a real Datashare)

Env note: this repo's Python venv is 3.12, and the dev group's `matplotlib`→`numpy 1.24.2` won't build there. Install runtime deps only: `poetry install --without dev`. Full `make test` needs a 3.10 env for the dev group.

Bring up a live corpus to exercise commands (e.g. `similar_docs`):

```bash
datashare &                                    # embedded mode: web :8080 + its own ES :9200
# Index a real folder into a dedicated project via CLI mode, reusing the embedded ES.
# OCR off (fast, skips Tesseract on images — they still index as image/* content types);
# in-memory datasource so it doesn't lock the embedded instance's SQLite DB.
datashare --mode CLI --stages SCAN,INDEX \
  --defaultProject research \
  --dataDir /path/to/folder \
  --elasticsearchAddress http://localhost:9200 \
  --ocr false \
  --dataSourceUrl 'jdbc:sqlite:file:memorydb.db?mode=memory&cache=shared'

poetry run tarentula similar-docs --datashare-project research --elasticsearch-url http://localhost:9200
```

For a richer corpus, `scripts/seed_test_corpus.sh` downloads 20 Newsgroups (labeled
topics → measurable query precision) + Govdocs1 zips (format diversity) and indexes
them into a `test-corpus` project on the same embedded ES.

`similar_docs` is interactive (`inquirer`), so it can't be driven headlessly — exercise its query methods directly (`SimilarDocs(...).query_all()` / `.count_matches()`) for automated checks.

## Tests

`tests/test_abstract.py::TestAbstract` is the base class: it stands up a `DatashareClient`, indexes fixture documents (`tests/fixtures/species.json`), and cleans up the index. Subclass it for anything needing indexed data.
