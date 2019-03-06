package main

import (
	"log"

	"github.com/blevesearch/bleve"
	"github.com/blevesearch/bleve/analysis/analyzer/custom"
	"github.com/blevesearch/bleve/analysis/lang/en"
	"github.com/blevesearch/bleve/analysis/token/lowercase"
	"github.com/blevesearch/bleve/analysis/token/porter"
	"github.com/blevesearch/bleve/analysis/tokenizer/unicode"
	"github.com/blevesearch/bleve/mapping"
)

const (
	AnalyzerName = "rabble"
)

func RabbleAnalyzer() map[string]interface{} {
	return map[string]interface{}{
		"type":         custom.Name,
		"char_filters": []string{},
		"tokenizer":    unicode.Name,
		"token_filters": []string{
			en.StopName,
			lowercase.Name,
			porter.Name,
		},
	}
}

func createIndexMapping() mapping.IndexMapping {
	indexMapping := bleve.NewIndexMapping()

	if err := indexMapping.AddCustomAnalyzer(AnalyzerName, RabbleAnalyzer()); err != nil {
		log.Fatal(err)
	}

	indexMapping.DefaultAnalyzer = "rabble"
	doc := mapping.NewDocumentStaticMapping()

	text := mapping.NewTextFieldMapping()

	// TODO(devoxel): figure out field mapping for creation timestamp
	doc.AddFieldMappingsAt("body", text)
	doc.AddFieldMappingsAt("title", text)
	doc.AddFieldMappingsAt("author", text)

	// This sets the document mapping such that any document added uses
	// the document mapping defined above. Since it's static, this only
	// searches explicitly declared fields.
	indexMapping.AddDocumentMapping("_default", doc)

	// TODO(devoxel): Ideally, we should annotate a PostsEntry type with
	// the Type() functions, allowing more complex search conversions
	// This allows custom character filters by type, or custom language
	// analysis by type.
	return indexMapping
}
