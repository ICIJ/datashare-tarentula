# Datashare Tarentula Cookbook 👩‍🍳

A pragmatic approach to learn how to use Datashare Tarentula.

## Export search query to CSV

Export documents metadata, including the author, for the query `query`:

```
tarentula export-by-query --query 'spider' --source 'metadata.tika_metadata_author'
```

Export documents metadata, including the author (falling back to `Jane Doe`), for the query `query`:

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

Export documents metadata for "france" on a remove server:

tarentula export-by-query --datashare-url "https://datashare-demo.icij.org" --datashare-project "luxleaks" --apikey "XXXXX" --query 'france' 
