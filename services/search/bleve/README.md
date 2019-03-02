# Bleve Search

This searcher internally uses [bleve](http://blevesearch.com/). This was 
chosen because it's a small dependency and is easy to work with.

For a large instance, a better solution would be Lucene or ElasticSearch. These
solutions aren't built-in at the time of writing, so you would have to write one
yourself.

## Properties

We have a preconfigured search that:

- Fuzzy matches (using levenshtein distance)
- Stems the index, using porter stemming.

Partial matching is limited to the fuzziness metric. This is due to the
costly nature of substring matching. Shingling would help prevent this but
requires ngram indexing, which greatly increases the index size.

Porter stemming work under the assumption that the indexed material is English.
A more complex multi-language approach could be possible, though the best
approach would be to sure up the localization as a whole and then explicitly add
certain mappings for certain languages.
