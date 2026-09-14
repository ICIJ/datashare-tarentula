# Datashare Tarentula Cookbook 👩‍🍳

A pragmatic approach to learn how to use Datashare Tarentula.

## Count matches of query

Count all files:

```
tarentula count
```
or
```
tarentula count --query '*'
```

Count files that match the query `spider`:

```
tarentula count --query 'spider'
```

## List metadata properties available

```
tarentula list-metadata
```

Include counting of docs by metadata property:


```
tarentula list-metadata --count
```

Filter results only for email kind of documents:


```
tarentula list-metadata --count --filter-by "contentType=message/rfc822"
```



## Export search query to CSV

Export documents metadata, including the author, for the query `spider`:

```
tarentula export-by-query --query 'spider' --source 'metadata.tika_metadata_author'
```

Export documents metadata, including the author (falling back to `Jane Doe`), for the query `spider`:

```
tarentula export-by-query --query 'spider' --source 'metadata.tika_metadata_author:Jane Doe'
```

Export documents metadata, including language, for all JSON files:

```
tarentula export-by-query --query 'contentType:"application/json"' --source 'language'
```

Export documents metadata, including creation date and author, for all PDF files:

```
tarentula export-by-query --query 'contentType:"application/pdf"' --source 'metadata.tika_metadata_creation_date,metadata.tika_metadata_author'
```

Export documents metadata for `france` on a remote server:

```
tarentula export-by-query --datashare-url "https://datashare-demo.icij.org" --datashare-project "luxleaks" --apikey "XXXXX" --query 'france'
```

## Run aggregations on Datashare Demo

Count number of occurrences of distinct values in a metadata property, classic `GROUP BY` and `COUNT` :

```
tarentula aggregate --apikey "XXXXXXXX" --datashare-url "https://datashare-demo.icij.org/" --datashare-project "luxleaks" --group-by language --run count
```

Return number of distinct values in a metadata property:

```
tarentula aggregate --apikey "XXXXXXXX" --datashare-url "https://datashare-demo.icij.org/" --datashare-project "luxleaks" --operation-field language --run nunique
```

Return yearly grouped values of creation_date property and count num of docs:

```
tarentula aggregate --apikey "XXXXXXXX" --datashare-url "https://datashare-demo.icij.org/" --datashare-project "luxleaks" --operation-field "metadata.tika_metadata_creation_date" --run date_histogram
```

Return monthly grouped values instead:

```
tarentula aggregate --apikey "XXXXXXXX" --datashare-url "https://datashare-demo.icij.org/" --datashare-project "luxleaks" --operation-field "metadata.tika_metadata_creation_date" --run date_histogram --calendar-interval month
```

Return basic number statistics:

```
tarentula aggregate --apikey "XXXXXXXX" --datashare-url "https://datashare-demo.icij.org/" --datashare-project "luxleaks" --operation-field contentLength --run stats
```

Return basic string statistics:

```
tarentula aggregate --apikey "XXXXXXXX" --datashare-url "https://datashare-demo.icij.org/" --datashare-project "luxleaks" --operation-field path --run string_stats

tarentula aggregate --apikey "XXXXXXXX" --datashare-url "https://datashare-demo.icij.org/" --datashare-project "luxleaks" --operation-field language --run string_stats
```

## Download documents

Download the files matching a query into `./tmp`:

```
tarentula download --query 'spider'
```

Download the first 100 PDF files into a directory of your choice:

```
tarentula download --query 'contentType:"application/pdf"' --destination-directory ./pdfs --limit 100
```

Lay the files out one directory per project, named after the original file, instead of the default `{id_2b}/{id_4b}/{id}`. The available placeholders are `id`, `id_2b`, `id_4b`, `project`, `basename` and `parentDocument`:

```
tarentula download --query 'spider' --path-format '{project}/{basename}'
```

Download the indexed JSON documents instead of the raw files, keeping only a few fields:

```
tarentula download --query 'spider' --no-raw-file --source 'path,contentType,language'
```

Skip the files already on disk, and go easy on the server with a 200ms pause between requests:

```
tarentula download --query 'spider' --once --throttle 200
```

## Tag documents from a CSV

Tag documents listed in a CSV file, with either a `documentId` column or a `documentUrl` one (see the [CSV formats](README.md#csv-formats)):

```
tarentula tagging tags.csv
```

Tag documents on a remote server:

```
tarentula tagging --datashare-url "https://datashare-demo.icij.org" --datashare-project "luxleaks" --apikey "XXXXXXXX" tags.csv
```

## Tag documents by query

Tag documents directly in the index, without going through Datashare, using a JSON file that maps each tag to an Elasticsearch query. See [this example](tests/fixtures/tags-by-content-type.json):

```
tarentula tagging-by-query tags-by-content-type.json
```

On a big index, let Elasticsearch work in the background and return a task id right away:

```
tarentula tagging-by-query --no-wait-for-completion tags-by-content-type.json
```

## Remove tags

Remove every tag from every document of the project:

```
tarentula clean-tags-by-query
```

Remove tags only from the documents matching an Elasticsearch query, given inline or as a file with `@`:

```
tarentula clean-tags-by-query --query '{"query":{"match":{"contentType":"application/pdf"}}}'
```

```
tarentula clean-tags-by-query --query @query.json
```
