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
  --syslog-address TEXT   Syslog address
  --syslog-port INTEGER   Syslog port
  --syslog-facility TEXT  Syslog facility
  --help                  Show this message and exit.

Commands:
  download
  tagging
```

## Tagging

A command to batch tag documents with a CSV file.

```
Usage: tarentula tagging [OPTIONS] CSV_PATH

Options:
  --datashare-url TEXT      Datashare URL
  --datashare-project TEXT  Datashare project
  --throttle INTEGER        Request throttling (in ms)
  --cookies TEXT            Key/value pair to add a cookie to each request to
                            the API. You can separate semicolons:
                            key1=val1;key2=val2;...
  --help                    Show this message and exit.
```

### CSV formats

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

## Tagging

A command to download all files matching a query.

```
Usage: tarentula download [OPTIONS]

Options:
  --datashare-url TEXT          Datashare URL
  --datashare-project TEXT      Datashare project
  --elasticsearch-url TEXT      You can additionally pass the Elasticsearch
                                URL in order to use scrolling capabilities of
                                Elasticsearch (useful when dealing with a lot
                                of results)

  --query TEXT                  The query string to filter documents
  --destination-directory TEXT  Directory documents will be downloaded
  --throttle INTEGER            Request throttling (in ms)
  --cookies TEXT                Key/value pair to add a cookie to each request
                                to the API. You can separate semicolons:
                                key1=val1;key2=val2;...

  --path-format TEXT            Downloaded document path template
  --help                        Show this message and exit.
```

## Testing

To test this tool, you must have Datashare and Elasticsearch running on your development machine. We provide a Docker Compose file to simplify the installation.

```
docker-compose -p tarentula -f tests/docker-compose.yml up
```

Install the development dependencies:

```
sudo apt install pipenv
make install
```

Then in a separated terminal, just run:

```
make test
```
