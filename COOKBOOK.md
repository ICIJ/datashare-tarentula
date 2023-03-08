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
tarentula list-metadata --count --filter_by "contentType=message/rfc822"
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

Export documents metadata for `france` on a remove server:

```
tarentula export-by-query --datashare-url "https://datashare-demo.icij.org" --datashare-project "luxleaks" --apikey "XXXXX" --query 'france'
```

## Run aggregations on Datashare Demo

Count number of occurrences of distinct values in a metadata property, classic `GROUP BY` and `COUNT` :

```
tarentula aggregate --apikey "XXXXXXXX" --datashare-url "https://datashare-demo.icij.org/" --datashare-project "luxleaks" --group_by language --run count
```

Return number of distinct values in a metadata property:

```
tarentula aggregate --apikey "XXXXXXXX" --datashare-url "https://datashare-demo.icij.org/" --datashare-project "luxleaks" --operation_field language --run nunique
```

Return yearly grouped values of creation_date property and count num of docs:

```
tarentula aggregate --apikey "XXXXXXXX" --datashare-url "https://datashare-demo.icij.org/" --datashare-project "luxleaks" --operation_field "metadata.tika_metadata_creation_date" --run date_histogram
```

Return basic number statistics:

```
tarentula aggregate --apikey "XXXXXXXX" --datashare-url "https://datashare-demo.icij.org/" --datashare-project "luxleaks" --operation_field contentLength --run stats
```

Return basic sting statistics:

```
tarentula aggregate --apikey "XXXXXXXX" --datashare-url "https://datashare-demo.icij.org/" --datashare-project "luxleaks" --operation_field path --run string_stats

tarentula aggregate --apikey "XXXXXXXX" --datashare-url "https://datashare-demo.icij.org/" --datashare-project "luxleaks" --operation_field language --run string_stats
```
