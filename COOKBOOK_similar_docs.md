# Similar Docs Cookbook 🕸️

`tarentula similar-docs` is an interactive session that helps you **converge on a
saved Elasticsearch query that retrieves documents similar to the ones you care
about** — maximizing the documents you targeted while minimizing false positives.

You start broad, narrow by facets, hand-pick example documents, and iterate:
each round the command derives a `more_like_this` query from your choices, shows
you how well it performs, and lets you correct it by marking false positives and
tuning the term lists. When you are happy, the query is saved as a JSON file you
can feed back to any other tarentula command.

## How it works

```
 initial query (2-3 broad words)
        │
        ▼
 Step 1/2: narrow by content type ──▶ language   (counts re-aggregate after each pick)
 Step 2/2: narrow by file size
        │
        ▼
 pick 2+ example docs  (metadata table + text blurb shown for each)
        │
        ▼
 common lines / ngrams between picks ──▶ choose the ones that matter
        │
        ▼
 top salient terms of your picks (significant_text) ──▶ add some to the query
        │
        ▼
 query = more_like_this(your docs)  AND  (at least minimum_should_match of chosen terms)
        │
        ▼
 narrow the new results by facets again
 precision report: "N/M of your selected docs still match"
        │
        ▼
 mark false positives ──▶ excluded as `unlike` docs next round
 top terms of all unliked docs so far (minus anything in your liked terms)
   ──▶ exclude some as NOT clauses
        │
        ▼
 status report: current query JSON + hit count + facet breakdown
        │
        ├──▶ "No, keep going"  → next round
        ├──▶ "Yes, save current query and leave"  → writes the JSON file
        └──▶ "No, give it up"
```

Positive and negative term lists **persist across rounds** and end up in the
saved query, so the exported JSON carries the full vocabulary of what you liked
and rejected.

## Quick start

```bash
tarentula similar-docs \
    --datashare-project my-project \
    --elasticsearch-url http://localhost:9200
```

<!-- TODO capture: initial query prompt + first facet step (test-corpus) -->
![Initial query prompt and facet narrowing](docs/captures/simdocs-01-query-and-facets.png)

## Options

| Option | Default | Notes |
|---|---|---|
| `--datashare-url` | `http://localhost:8080` | Datashare instance |
| `--datashare-project` | `local-datashare` | Project (= ES index) to search |
| `--elasticsearch-url` | *(none)* | Talk to ES directly instead of Datashare's proxy |
| `--query` | `*` | Starting query. If left as `*` you are prompted for one interactively |
| `--output-file` | `query-similar-docs.json` | Where the final query is saved |
| `--source` | metadata fields | Comma-separated fields shown for each doc |
| `--sort-by` / `--order-by` | `_score` / `desc` | Result ordering |
| `--apikey` / `--cookies` | *(none)* | Auth against a protected Datashare |

## Walkthrough

### 1. Start from a broad query

Two or three words are enough — the point is to get a rough, heterogeneous
batch to narrow down. An empty query (all docs) also works.

```
$ tarentula similar-docs --datashare-project test-corpus --elasticsearch-url http://localhost:9200
Start with a broad query (2-3 words; empty = all docs): motorcycle racing
Num of matches: 143
```

### 2. Narrow by facets, in two steps

First content type and language, then file size. **Counts re-aggregate after
every selection**: if you keep 67 PDFs, the language options shown next sum
to 67. Checking nothing keeps everything.

<!-- TODO capture: facet steps with narrowed counts (test-corpus) -->
![Facet narrowing with live counts](docs/captures/simdocs-02-facet-counts.png)

### 3. Pick 2+ example documents

Each candidate is listed in a table — id, type, language, size, name and the
first ~80 characters of its text — so text documents are tellable apart at a
glance. Select with `space`, confirm with `enter`.

If you select fewer than 2, you choose between **Show more results** (next
page, wrapping around at the end) and **Exit** (leave cleanly, nothing saved).
`Ctrl-C` on any prompt also backs you out safely.

<!-- TODO capture: docs table + checkbox picker (test-corpus) -->
![Document picker with metadata table](docs/captures/simdocs-03-doc-picker.png)

### 4. Choose commonalities and query terms

The command extracts lines (falling back to ngrams) shared by all your picks,
ranks them by whole-index rarity (rarest first — those are the distinctive,
narrowing ones), and asks which matter. Then it surfaces the **most salient
terms** of your picks relative to the whole index (`significant_text`) and
offers to add them to the query. Both go in as `should` `match_phrase`
clauses — not blended into `more_like_this`, so a term you picked has to
actually appear in the document rather than just nudge the fuzzy MLT score.
How many of them are required is `--minimum-should-match`'s percentage
applied to your picked terms and rounded up, floored at 1 so it can never
silently disable itself (ES's own percentage handling would floor a small
`should` list like this to 0 and require none of them).

### 5. Review results, mark false positives

The `more_like_this` results go through another facet-narrowing pass, then:

```
Num of matches after filtering: 31
3/3 of your selected docs still match
```

The precision line tells you whether the derived query still captures your
examples. Mark any wrong results as **false positives**: they're excluded as
`unlike` documents in `more_like_this` from now on. Their salient terms — and
those of every unliked doc marked so far, not just this round's — are then
offered as exclusions; any term also salient among your liked picks is
dropped from the offer first, since that wouldn't discriminate. Picked terms
become `must_not` clauses, a hard exclusion rather than a fuzzy nudge.

<!-- TODO capture: precision report + false-positive marking (test-corpus) -->
![Precision report and false positives](docs/captures/simdocs-04-false-positives.png)

### 6. Read the status report, iterate or save

Before asking whether to continue, the command prints where you stand: the
current query as JSON, its hit count, and the facet breakdown of its results.
Iterate until the numbers look right, then save.

```
Matches: 29
  content_types: application/pdf (29)
  languages: ENGLISH (28), SPANISH (1)
  sizes: 100 KB - 1 MB (16), > 1 MB (13)
```

## Recipes

### Reuse the saved query with other tarentula commands

Any command accepting `--query` treats an `@`-prefixed value as a JSON file:

```bash
tarentula count --query @query-similar-docs.json
tarentula export-by-query --query @query-similar-docs.json --output-file similar.csv
tarentula tagging-by-query my-tag --query @query-similar-docs.json
```

### Resume from a saved query

Pass the saved file back as the starting query to keep refining it later:

```bash
tarentula similar-docs --query @query-similar-docs.json --output-file query-v2.json
```

### Build a test corpus to practice on

`scripts/seed_test_corpus.sh` downloads 20 Newsgroups (~19k text docs in 20
labeled topic folders — ground truth to sanity-check a derived query) and
Govdocs1 zips (mixed PDF/DOC/XLS/HTML — real facet diversity), then indexes
them into a `test-corpus` project on your local embedded Datashare:

```bash
datashare &                          # embedded mode: web :8080 + ES :9200
scripts/seed_test_corpus.sh 2        # 2 govdocs zips ≈ 600 MB download
tarentula similar-docs --datashare-project test-corpus --elasticsearch-url http://localhost:9200
```

### Judge query quality with labeled data

With 20 Newsgroups indexed, pick 2-3 documents from one topic folder (the
`path` contains the topic, e.g. `rec.motorcycles`) and save the derived query.
Then measure how well it isolates the topic:

```bash
tarentula export-by-query --query @query-similar-docs.json --source path --output-file hits.csv
awk -F, '{print ($0 ~ /rec.motorcycles/) ? "hit" : "miss"}' hits.csv | sort | uniq -c
```

## Notes & limits

- Images index with empty text (OCR off in the seed script), so blurbs and
  `more_like_this` have nothing to work with — the command is text-driven.
- `more_like_this` parameters are tunable via `--max-query-terms` (30),
  `--min-term-freq` (1), `--min-doc-freq` (10), `--min-word-length` (4) and
  `--minimum-should-match` (30%). On small indexes or short documents, lower
  `--min-doc-freq`; raise `--minimum-should-match` for stricter results.
- Every offered term shows a doc count: commonalities show how many docs in
  the whole index contain the phrase (high = boilerplate — picking it will
  broaden the query), salient terms show how many of your picked docs (or
  false positives) contain them.
- The saved query includes your seed documents by id (`include: true`), the
  facet filters, and both term lists — it is self-contained and portable to
  any tool that speaks the ES query DSL against the same index.
