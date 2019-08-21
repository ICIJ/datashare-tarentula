# Datashare Tarentula [![CircleCI](https://circleci.com/gh/ICIJ/datashare-tarentula.svg?style=svg)](https://circleci.com/gh/ICIJ/datashare-tarentula)

CSV manipulation cli for [Datashare](https://datashare.icij.org).

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
  --help                    Show this message and exit.
```
