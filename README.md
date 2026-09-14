# Datashare Tarentula [![CI](https://github.com/ICIJ/datashare-tarentula/actions/workflows/ci.yml/badge.svg)](https://github.com/ICIJ/datashare-tarentula/actions/workflows/ci.yml)

Cli toolbelt for [Datashare](https://datashare.icij.org).

```
     /      \
  \  \  ,,  /  /
   '-.`\()/`.-'
  .--_'(  )'_--.
 / /` /`""`\ `\ \
  |  |  ><  |  |
  \  \      /  /
      '.__.'

Usage: tarentula [OPTIONS] COMMAND [ARGS]...

Options:
  --version               Show the version and exit.
  --syslog-address TEXT   Syslog address
  --syslog-port TEXT      Syslog port
  --syslog-facility TEXT  Syslog facility
  --stdout-loglevel TEXT  Change the default log level for stdout error
                          handler
  --help                  Show this message and exit.

Commands:
  aggregate
  clean-tags-by-query
  count
  download
  export-by-query
  list-metadata
  tagging
  tagging-by-query
```

---
<!-- TOC depthFrom:2 depthTo:6 withLinks:1 updateOnSave:1 orderedList:0 -->

- [Installation](#installation)
- [Usage](#usage)
  - [Cookbook 👩‍🍳](#cookbook-)
  - [Count](#count)
  - [Clean Tags by Query](#clean-tags-by-query)
  - [Download](#download)
  - [Export by Query](#export-by-query)
  - [Tagging](#tagging)
    - [CSV formats](#csv-formats)
  - [Tagging by Query](#tagging-by-query)
  - [List Metadata](#list-metadata)
  - [Aggregate](#aggregate)
  - [Following your changes](#following-your-changes)
- [Configuration File](#configuration-file)
- [Testing](#testing)
- [Releasing](#releasing)
  - [Manual fallback](#manual-fallback)

<!-- /TOC -->
---

## Installation

You can install Datashare Tarentula with your favorite package manager:

```
pip3 install --user tarentula
```

Or alternatively with Docker:

```
docker run icij/datashare-tarentula
```

## Usage

Datashare Tarentula comes with basic commands to interact with a Datashare instance (running locally or on a remote server). Primarily focus on bulk actions, it provides you with both a cli interface and a python API.

### Cookbook 👩‍🍳

To learn more about how to use Datashare Tarentula with a list of examples, please refer to <a href="./COOKBOOK.md">the Cookbook</a>.

### Count

A command to just count the number of files matching a query.

```
Usage: tarentula count [OPTIONS]

Options:
  --apikey TEXT                  Datashare authentication apikey
  --datashare-url TEXT           Datashare URL
  --datashare-project TEXT       Datashare project
  --elasticsearch-url TEXT       You can additionally pass the Elasticsearch
                                 URL in order to use scrolling capabilities of
                                 Elasticsearch (useful when dealing with a lot
                                 of results)
  --query TEXT                   The query string to filter documents
  --cookies TEXT                 Key/value pair to add a cookie to each
                                 request to the API. You can separate
                                 semicolons: key1=val1;key2=val2;...
  --traceback / --no-traceback   Display a traceback in case of error
  --type [Document|NamedEntity]  Type of indexed documents to download
  --help                         Show this message and exit.
```

### Clean Tags by Query

A command that uses Elasticsearch `update-by-query` feature to batch untag documents directly in the index.

```
Usage: tarentula clean-tags-by-query [OPTIONS]

Options:
  --apikey TEXT                   Datashare authentication apikey
  --datashare-project TEXT        Datashare project
  --elasticsearch-url TEXT        Elasticsearch URL which is used to perform
                                  update by query
  --cookies TEXT                  Key/value pair to add a cookie to each
                                  request to the API. You can separate
                                  semicolons: key1=val1;key2=val2;...
  --wait-for-completion / --no-wait-for-completion
                                  Create a Elasticsearch task to perform the
                                  update asynchronously
  --query TEXT                    Give a JSON query to filter documents that
                                  will have their tags cleaned. It can be a
                                  file with @path/to/file. Default to all.
  --help                          Show this message and exit.
```

### Download

A command to download all files matching a query.

```
Usage: tarentula download [OPTIONS]

Options:
  --apikey TEXT                   Datashare authentication apikey
  --datashare-url TEXT            Datashare URL
  --datashare-project TEXT        Datashare project
  --elasticsearch-url TEXT        You can additionally pass the Elasticsearch
                                  URL in order to use scrolling capabilities
                                  of Elasticsearch (useful when dealing with a
                                  lot of results)
  --query TEXT                    The query string to filter documents
  --destination-directory TEXT    Directory documents will be downloaded
  --throttle INTEGER              Request throttling (in ms)
  --cookies TEXT                  Key/value pair to add a cookie to each
                                  request to the API. You can separate
                                  semicolons: key1=val1;key2=val2;...
  --path-format TEXT              Downloaded document path template
  --scroll TEXT                   Scroll duration
  --source TEXT                   A comma-separated list of field to include
                                  in the downloaded document from the index
  -l, --limit INTEGER             Limit the total results to return
  -f, --from INTEGER              Passed to the search it will bypass the
                                  first n documents
  --size INTEGER                  Size of the scroll request that powers the
                                  operation.
  --sort-by TEXT                  Field to use to sort results
  --order-by [asc|desc]           Order to use to sort results
  --once / --not-once             Download file only once
  --traceback / --no-traceback    Display a traceback in case of error
  --progressbar / --no-progressbar
                                  Display a progressbar
  --raw-file / --no-raw-file      Download raw file from Datashare
  --type [Document|NamedEntity]   Type of indexed documents to download
  --help                          Show this message and exit.
```

### Export by Query

A command to export all files matching a query.

```
Usage: tarentula export-by-query [OPTIONS]

Options:
  --apikey TEXT                   Datashare authentication apikey
  --datashare-url TEXT            Datashare URL
  --datashare-project TEXT        Datashare project
  --elasticsearch-url TEXT        You can additionally pass the Elasticsearch
                                  URL in order to use scrolling capabilities
                                  of Elasticsearch (useful when dealing with a
                                  lot of results)
  --query TEXT                    The query string to filter documents
  --output-file TEXT              Path to the CSV file
  --throttle INTEGER              Request throttling (in ms)
  --cookies TEXT                  Key/value pair to add a cookie to each
                                  request to the API. You can separate
                                  semicolons: key1=val1;key2=val2;...
  --scroll TEXT                   Scroll duration
  --source TEXT                   A comma-separated list of field to include
                                  in the export
  --sort-by TEXT                  Field to use to sort results
  --order-by [asc|desc]           Order to use to sort results
  --traceback / --no-traceback    Display a traceback in case of error
  --progressbar / --no-progressbar
                                  Display a progressbar
  --type [Document|NamedEntity|Duplicate]
                                  Type of indexed documents to download
  --size INTEGER                  Size of the scroll request that powers the
                                  operation.
  -f, --from INTEGER              Passed to the search it will bypass the
                                  first n documents
  -l, --limit INTEGER             Limit the total results to return
  --query-field / --no-query-field
                                  Add the query to the export CSV
  --help                          Show this message and exit.
```

### Tagging

A command to batch tag documents with a CSV file.

```
Usage: tarentula tagging [OPTIONS] CSV_PATH

Options:
  --apikey TEXT                   Datashare authentication apikey
  --datashare-url TEXT            Datashare URL
  --datashare-project TEXT        Datashare project
  --throttle INTEGER              Request throttling (in ms)
  --cookies TEXT                  Key/value pair to add a cookie to each
                                  request to the API. You can separate
                                  semicolons: key1=val1;key2=val2;...
  --traceback / --no-traceback    Display a traceback in case of error
  --progressbar / --no-progressbar
                                  Display a progressbar
  --help                          Show this message and exit.
```

#### CSV formats

Tagging with a `documentId` and `routing`:

```csv
tag,documentId,routing
Actinopodidae,l7VnZZEzg2fr960NWWEG,l7VnZZEzg2fr960NWWEG
Antrodiaetidae,DWLOskax28jPQ2CjFrCo
Atracidae,6VE7cVlWszkUd94XeuSd,vZJQpKQYhcI577gJR0aN
Atypidae,DbhveTJEwQfJL5Gn3Zgi,DbhveTJEwQfJL5Gn3Zgi
Barychelidae,DbhveTJEwQfJL5Gn3Zgi,DbhveTJEwQfJL5Gn3Zgi
```

When `routing` is missing, the `documentId` is used instead.

Tagging with a `documentUrl`:

```csv
tag,documentUrl
Mecicobothriidae,http://localhost:8080/#/ds/local-datashare/DbhveTJEwQfJL5Gn3Zgi/DbhveTJEwQfJL5Gn3Zgi
Microstigmatidae,http://localhost:8080/#/d/local-datashare/iuL6GUBpO7nKyfSSFaS0/iuL6GUBpO7nKyfSSFaS0
Migidae,http://localhost:8080/#/e/local-datashare/BmovvXBisWtyyx6o9cuG/BmovvXBisWtyyx6o9cuG
Nemesiidae,http://localhost:8080/#/dm/local-datashare/vZJQpKQYhcI577gJR0aN/vZJQpKQYhcI577gJR0aN
Paratropididae,http://localhost:8080/#/ds/local-datashare/vYl1C4bsWphUKvXEBDhM
```

The `d`, `e`, `ds` and `dm` document routes are all accepted, with or without the trailing routing segment, and a query string is ignored. Any other URL shape stops the command with an error.

### Tagging by Query

A command that uses Elasticsearch `update-by-query` feature to batch tag documents directly in the index.

To see an example of input file, refer to [this JSON](tests/fixtures/tags-by-content-type.json).

```
Usage: tarentula tagging-by-query [OPTIONS] JSON_PATH

Options:
  --apikey TEXT                   Datashare authentication apikey
  --datashare-project TEXT        Datashare project
  --elasticsearch-url TEXT        Elasticsearch URL which is used to perform
                                  update by query
  --throttle INTEGER              Request throttling (in ms)
  --cookies TEXT                  Key/value pair to add a cookie to each
                                  request to the API. You can separate
                                  semicolons: key1=val1;key2=val2;...
  --traceback / --no-traceback    Display a traceback in case of error
  --progressbar / --no-progressbar
                                  Display a progressbar
  --wait-for-completion / --no-wait-for-completion
                                  Create a Elasticsearch task to perform the
                                  update asynchronously
  --scroll-size INTEGER           Size of the scroll request that powers the
                                  operation.
  --help                          Show this message and exit.
```

### List Metadata

You can list the metadata from the mapping, optionally counting the number of occurrences of each field in the index, with the `--count` parameter. Counting the fields is disabled by default.

It includes a `--filter-by` parameter to narrow retrieving metadata properties of specific sets of documents. For instance it can be used to get just emails related properties with: `--filter-by "contentType=message/rfc822"`

```
Usage: tarentula list-metadata [OPTIONS]

Options:
  --datashare-url TEXT           Datashare URL
  --datashare-project TEXT       Datashare project
  --elasticsearch-url TEXT       You can additionally pass the Elasticsearch
                                 URL in order to use scrolling capabilities of
                                 Elasticsearch (useful when dealing with a lot
                                 of results)
  --apikey TEXT                  Datashare authentication apikey
  --cookies TEXT                 Key/value pair to add a cookie to each
                                 request to the API. You can separate
                                 semicolons: key1=val1;key2=val2;...
  --traceback / --no-traceback   Display a traceback in case of error
  --type [Document|NamedEntity]  Type of indexed documents to get metadata
  --filter-by, --filter_by TEXT  Filter documents by pairs concatenated by
                                 coma of field names and values separated by
                                 =. Example "contentType=message/rfc822,conten
                                 tType=message/rfc822"
  --count / --no-count           Count or not the number of docs for each
                                 property found
  --help                         Show this message and exit.
```

### Aggregate

You can run aggregations on the data, the ElasticSearch aggregations API is partially enabled with this command.
The possibilities are:

- count: grouping by a given field different values, and count the num of docs.
- nunique: returns the number of unique values of a given field.
- date_histogram: returns counting of monthly or yearly grouped values for a given date field.
- sum: returns the sum of values of number type fields.
- min: returns the min of values of number type fields.
- max: returns the max of values of number type fields.
- avg: returns the average of values of number type fields.
- stats: returns a bunch of statistics for a given number type fields.
- string_stats: returns a bunch of string statistics for a given string type fields.

```
Usage: tarentula aggregate [OPTIONS]

Options:
  --apikey TEXT                   Datashare authentication apikey
  --datashare-url TEXT            Datashare URL
  --datashare-project TEXT        Datashare project
  --elasticsearch-url TEXT        You can additionally pass the Elasticsearch
                                  URL in order to use scrolling capabilities
                                  of Elasticsearch (useful when dealing with a
                                  lot of results)
  --query TEXT                    The query string to filter documents
  --cookies TEXT                  Key/value pair to add a cookie to each
                                  request to the API. You can separate
                                  semicolons: key1=val1;key2=val2;...
  --traceback / --no-traceback    Display a traceback in case of error
  --type [Document|NamedEntity]   Type of indexed documents to download
  --group-by, --group_by TEXT     Field to use to aggregate results
  --operation-field, --operation_field TEXT
                                  Field to run the operation on
  --run [count|nunique|date_histogram|sum|stats|string_stats|min|max|avg]
                                  Operation to run
  --calendar-interval, --calendar_interval [year|month]
                                  Calendar interval for date histogram
                                  aggregation
  --help                          Show this message and exit.
```

### Following your changes

When running Elasticsearch changes on big datasets, it could take a very long time. As we were curling ES to see if the task was still running well, we added a small utility to follow the changes. It makes a live graph of a provided ES indicator with a specified filter.

It uses [matplotlib](https://matplotlib.org/) and python3-tk. Neither is installed by the published package: run it from a clone, after `make install`.

```
poetry run python -m tarentula.graph_realtime
```

If you see the following message :

```
graph_realtime.py:32: UserWarning: Matplotlib is currently using agg, which is a non-GUI backend, so cannot show the figure
```

Then you have to install [tkinter](https://docs.python.org/3/library/tkinter.html), i.e. python3-tk for Debian/Ubuntu.

The command has the options below:

```
Usage: python -m tarentula.graph_realtime [OPTIONS]

Options:
  --query TEXT                Give a JSON query to filter documents. It can be
                              a file with @path/to/file. Default to all.
  --index TEXT                Elasticsearch index (default local-datashare)
  --refresh-interval INTEGER  Graph refresh interval in seconds (default 5)
  --field TEXT                Field indicator to display over time (default
                              hits.total.value)
  --elasticsearch-url TEXT    Elasticsearch URL which is used to perform
                              update by query
  --help                      Show this message and exit.
```

## Configuration File

Tarentula supports several sources for configuring its behavior, including an ini files and command-line options.

Configuration file will be searched for in the following order (use the first file found, all others are ignored):

  * `TARENTULA_CONFIG` (environment variable if set)
  * `tarentula.ini` (in the current directory)
  * `~/.tarentula.ini` (in the home directory)
  * `/etc/tarentula/tarentula.ini`

It should follow the following format (all values bellow are optional):

```
[DEFAULT]
apikey = SECRETHALONOPROCTIDAE
datashare_url = http://here:8080
datashare_project = local-datashare

[logger]
syslog_address = 127.0.0.0
syslog_port = 514
syslog_facility = local7
stdout_loglevel = INFO
```

## Testing

To test this tool, you must have Datashare and Elasticsearch running on your development machine.

After you [installed Datashare](https://datashare.icij.org/), just run it with a test project/user:

```
datashare -p test-datashare -u test
```

In a separate terminal, install the development dependencies:

```
make install
```

Finally, run the test

```
make test
```

Run `make help` to see every available target.

## Releasing

Releases are automated, nothing has to be run by hand.

Every push runs the [`CI` workflow](.github/workflows/ci.yml): lint, then the test suite against a real Datashare on Python 3.9 to 3.12. When that run is on `main` and it passes, it triggers the [`Release` workflow](.github/workflows/release.yml), which:

1. Works out the next version from the commit messages with [Python Semantic Release](https://python-semantic-release.readthedocs.io/), bumps `pyproject.toml`, updates `CHANGELOG.md`, commits, tags and creates the GitHub release.
2. Publishes the package to [PyPI](https://pypi.org/project/tarentula/) using trusted publishing, so no token is stored in the repository.
3. Builds the `linux/amd64` and `linux/arm64` images from the new tag and pushes them to [Docker Hub](https://hub.docker.com/repository/docker/icij/datashare-tarentula), as `:<version>` and `:latest`.

Tags are the bare version, `4.5.2`, not `v4.5.2`; the `v`-prefixed tags predate the automation and are ignored.

Steps 2 and 3 only run when step 1 actually produced a version. The whole workflow is skipped outside the `ICIJ/datashare-tarentula` repository, so forks never publish.

What decides the version is the commit subject, which follows [Conventional Commits](https://www.conventionalcommits.org/):

| Commit subject | Release |
| --- | --- |
| `fix: ...` or `perf: ...` | patch |
| `feat: ...` | minor |
| `feat!: ...`, or any commit with a `BREAKING CHANGE:` footer | major |
| `build:`, `chore:`, `ci:`, `docs:`, `refactor:`, `style:`, `test:` | none |

Commits inside a squash-merged pull request are read too, so a squashed branch still releases what its commits say. Merge commits are ignored.

Follow the run on the [Actions tab](https://github.com/ICIJ/datashare-tarentula/actions/workflows/release.yml). When no commit calls for a release, the workflow succeeds and publishes nothing. You can also start it by hand from that page ("Run workflow"), which always releases from `main` whatever branch you pick in the dropdown.

### Manual fallback

If the CI workflow is unavailable, you can publish from your machine. This requires being a maintainer of the PyPI project and a member of the ICIJ organization on Docker Hub, with credentials configured locally.

Bump the version yourself first, since nothing else will:

```
poetry version patch
```

Publish to PyPI:

```
make distribute
```

Build and push the multi-arch Docker image (run `make docker-setup-multiarch` once to configure buildx, see the [Docker documentation](https://docs.docker.com/build/building/multi-platform/)):

```
make docker-publish
```
