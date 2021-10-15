# Datashare Tarentula [![CircleCI](https://circleci.com/gh/ICIJ/datashare-tarentula.svg?style=svg)](https://circleci.com/gh/ICIJ/datashare-tarentula)

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
  --syslog-address      TEXT    localhost   Syslog address
  --syslog-port         INTEGER 514         Syslog port
  --syslog-facility     TEXT    local7      Syslog facility
  --stdout-loglevel     TEXT    ERROR       Change the default log level for stdout error handler
  --help                                    Show this message and exit
  --version                                 Show the installed version of Tarentula

Commands:
  count
  clean-tags-by-query
  download
  export-by-query
  tagging
  tagging-by-query
```

---
<!-- TOC depthFrom:2 depthTo:6 withLinks:1 updateOnSave:1 orderedList:0 -->

- [Usage](#usage)
	- [Cookbook 👩‍🍳](#cookbook-)
	- [Count](#count)
	- [Clean Tags by Query](#clean-tags-by-query)
	- [Download](#download)
	- [Export by Query](#export-by-query)
	- [Tagging](#tagging)
		- [CSV formats](#csv-formats)
	- [Tagging by Query](#tagging-by-query)
	- [Following your changes](#following-your-changes)
- [Configuration File](#configuration-file)
- [Testing](#testing)
- [Releasing](#releasing)
	- [1. Create a new release](#1-create-a-new-release)
	- [2. Upload distributions on pypi](#2-upload-distributions-on-pypi)
	- [3. Build and publish the Docker image](#3-build-and-publish-the-docker-image)
	- [4. Push your changes on Github](#4-push-your-changes-on-github)

<!-- /TOC -->
---

## Usage

Datashare Tarentula comes with basic commands to interact with a Datashare instance (running locally or on a remote server). Primarily focus on bulk actions, it provides you with both a cli interface and a python API.

### Cookbook 👩‍🍳

To learn more about how to use Datashare Tarentula with a list of examples, please refer to <a href="./COOKBOOK.md">the Cookbook</a>.

### Count

A command to just count the number of files matching a query.

```
Usage: tarentula count [OPTIONS]

Options:
  --datashare-url           TEXT        Datashare URL
  --datashare-project       TEXT        Datashare project
  --elasticsearch-url       TEXT        You can additionally pass the Elasticsearch
                                          URL in order to use scrollingcapabilities of
                                          Elasticsearch (useful when dealing with a
                                          lot of results)
  --query                   TEXT        The query string to filter documents
  --cookies                 TEXT        Key/value pair to add a cookie to each
                                          request to the API. You can
                                          separatesemicolons: key1=val1;key2=val2;...
  --apikey                  TEXT        Datashare authentication apikey
                                          in the downloaded document from the index
  --traceback / --no-traceback          Display a traceback in case of error
  --type [Document|NamedEntity]         Type of indexed documents to download
  --help                                Show this message and exit
```

### Clean Tags by Query

A command that uses Elasticsearch `update-by-query` feature to batch untag documents directly in the index.

```
Usage: tarentula clean-tags-by-query [OPTIONS]

Options:
  --datashare-project       TEXT        Datashare project
  --elasticsearch-url       TEXT        Elasticsearch URL which is used to perform
                                          update by query
  --cookies                 TEXT        Key/value pair to add a cookie to each
                                          request to the API. You can
                                          separatesemicolons: key1=val1;key2=val2;...
  --apikey                  TEXT        Datashare authentication apikey
  --traceback / --no-traceback          Display a traceback in case of error
  --wait-for-completion / --no-wait-for-completion
                                        Create a Elasticsearch task to perform the
                                          updateasynchronously
  --query                   TEXT        Give a JSON query to filter documents that
                                          will have their tags cleaned. It can be
                                          afile with @path/to/file. Default to all.
  --help                                Show this message and exit
```

### Download

A command to download all files matching a query.

```
Usage: tarentula download [OPTIONS]

Options:
  --datashare-url           TEXT        Datashare URL
  --datashare-project       TEXT        Datashare project
  --elasticsearch-url       TEXT        You can additionally pass the Elasticsearch
                                          URL in order to use scrollingcapabilities of
                                          Elasticsearch (useful when dealing with a
                                          lot of results)
  --query                   TEXT        The query string to filter documents
  --destination-directory   TEXT        Directory documents will be downloaded
  --throttle                INTEGER     Request throttling (in ms)
  --cookies                 TEXT        Key/value pair to add a cookie to each
                                          request to the API. You can
                                          separatesemicolons: key1=val1;key2=val2;...
  --apikey                  TEXT        Datashare authentication apikey
  --path-format             TEXT        Downloaded document path template
  --scroll                  TEXT        Scroll duration
  --source                  TEXT        A comma-separated list of field to include
                                          in the downloaded document from the index
  --once / --not-once                   Download file only once
  --traceback / --no-traceback          Display a traceback in case of error
  --progressbar / --no-progressbar      Display a progressbar
  --raw-file / --no-raw-file            Download raw file from Datashare
  --type [Document|NamedEntity]         Type of indexed documents to download
  --help                                Show this message and exit
```


### Export by Query

A command to export all files matching a query.

```
Usage: tarentula export-by-query [OPTIONS]

Options:
  --datashare-url TEXT            Datashare URL
  --datashare-project TEXT        Datashare project
  --elasticsearch-url TEXT        You can additionally pass the Elasticsearch
                                  URL in order to use scrollingcapabilities of
                                  Elasticsearch (useful when dealing with a
                                  lot of results)

  --query TEXT                    The query string to filter documents
  --output-file TEXT              Path to the CSV file
  --throttle INTEGER              Request throttling (in ms)
  --cookies TEXT                  Key/value pair to add a cookie to each
                                  request to the API. You can
                                  separatesemicolons: key1=val1;key2=val2;...

  --apikey TEXT                   Datashare authentication apikey
  --scroll TEXT                   Scroll duration
  --source TEXT                   A comma-separated list of field to include
                                  in the export

  --once / --not-once             Download file only once
  --traceback / --no-traceback    Display a traceback in case of error
  --progressbar / --no-progressbar
                                  Display a progressbar
  --type [Document|NamedEntity]   Type of indexed documents to download
  --help                          Show this message and exit.
```


### Tagging

A command to batch tag documents with a CSV file.

```
Usage: tarentula tagging [OPTIONS] CSV_PATH

Options:
  --datashare-url       TEXT        http://localhost:8080   Datashare URL
  --datashare-project   TEXT        local-datashare         Datashare project
  --throttle            INTEGER     0                       Request throttling (in ms)
  --cookies             TEXT        _Empty string_          Key/value pair to add a cookie to each request to the API. You can separate semicolons: key1=val1;key2=val2;...
  --apikey              TEXT        None                    Datashare authentication apikey
  --traceback / --no-traceback                              Display a traceback in case of error
  --progressbar / --no-progressbar                          Display a progressbar
  --help                                                    Show this message and exit
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

Tagging with a `documentUrl`:

```csv
tag,documentUrl
Mecicobothriidae,http://localhost:8080/#/d/local-datashare/DbhveTJEwQfJL5Gn3Zgi/DbhveTJEwQfJL5Gn3Zgi
Microstigmatidae,http://localhost:8080/#/d/local-datashare/iuL6GUBpO7nKyfSSFaS0/iuL6GUBpO7nKyfSSFaS0
Migidae,http://localhost:8080/#/d/local-datashare/BmovvXBisWtyyx6o9cuG/BmovvXBisWtyyx6o9cuG
Nemesiidae,http://localhost:8080/#/d/local-datashare/vZJQpKQYhcI577gJR0aN/vZJQpKQYhcI577gJR0aN
Paratropididae,http://localhost:8080/#/d/local-datashare/vYl1C4bsWphUKvXEBDhM/vYl1C4bsWphUKvXEBDhM
Porrhothelidae,http://localhost:8080/#/d/local-datashare/fgCt6JLfHSl160fnsjRp/fgCt6JLfHSl160fnsjRp
Theraphosidae,http://localhost:8080/#/d/local-datashare/WvwVvNjEDQJXkwHISQIu/WvwVvNjEDQJXkwHISQIu
```

### Tagging by Query

A command that uses Elasticsearch `update-by-query` feature to batch tag documents directly in the index.

To see an example of input file, refer to [this JSON](tests/fixtures/tags-by-content-type.json).

```
Usage: tarentula tagging-by-query [OPTIONS] JSON_PATH

Options:
  --datashare-project       TEXT        Datashare project
  --elasticsearch-url       TEXT        Elasticsearch URL which is used to perform
                                          update by query
  --throttle                INTEGER     Request throttling (in ms)
  --cookies                 TEXT        Key/value pair to add a cookie to each
                                          request to the API. You can
                                          separatesemicolons: key1=val1;key2=val2;...
  --apikey                  TEXT        Datashare authentication apikey
  --traceback / --no-traceback          Display a traceback in case of error
  --progressbar / --no-progressbar      Display a progressbar
  --wait-for-completion / --no-wait-for-completion
                                        Create a Elasticsearch task to perform the
                                          updateasynchronously
  --help                                Show this message and exit
```

### Following your changes

When running Elasticsearch changes on big datasets, it could take a very long time. As we were curling ES to see if the task was still running well, we added a small utility to follow the changes. It makes a live graph of a provided ES indicator with a specified filter.

It uses [mathplotlib](https://matplotlib.org/) and python3-tk.

If you see the following message :

```
$ graph_es
graph_realtime.py:32: UserWarning: Matplotlib is currently using agg, which is a non-GUI backend, so cannot show the figure
```

Then you have to install [tkinter](https://docs.python.org/3/library/tkinter.html), i.e. python3-tk for Debian/Ubuntu.

The command has the options below:

```
$ graph_es --help
Usage: graph_es [OPTIONS]

Options:
  --query               TEXT        Give a JSON query to filter documents. It can be
                                      a file with @path/to/file. Default to all.
  --index               TEXT        Elasticsearch index (default local-datashare)
  --refresh-interval    INTEGER     Graph refresh interval in seconds (default 5s)
  --field               TEXT        Field value to display over time (default "hits.total")
  --elasticsearch-url   TEXT        Elasticsearch URL which is used to perform
                                      update by query (default http://elasticsearch:9200)
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
sudo apt install pipenv
make install
```

Finally, run the test

```
make test
```


## Releasing

The releasing process uses [bumpversion](https://pypi.org/project/bumpversion/) to manage versions of this package, [pypi](https://pypi.org/project/tarentula/) to publish the Python package and [Docker Hub](https://hub.docker.com/) for the Docker image.

### 1. Create a new release

```
make [patch|minor|major]
```

### 2. Upload distributions on pypi

_To be able to do this, you will need to be a maintainer of the [pypi](https://pypi.org/project/tarentula/) project._

```
make distribute
```

### 3. Build and publish the Docker image

To build and upload a new image on the [docker repository](https://hub.docker.com/repository/docker/icij/datashare-tarentula) :

_To be able to do this, you will need to be part of the ICIJ organization on docker_

```
make docker-publish
```

### 4. Push your changes on Github

Git push release and tag :

```
git push origin master --tags
```
