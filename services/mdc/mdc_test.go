package main

import (
	"context"
	"testing"

	pb "github.com/cpssd/rabble/services/proto"
)

func TestMarkdownToHTML(t *testing.T) {
	tests := []struct {
		in   string
		want string
	}{
		{
			in:   "## first \n\nI posted this blog first!",
			want: "<h2>first</h2>\n\n<p>I posted this blog first!</p>\n",
		},
		{
			in:   "**test**",
			want: "<p><strong>test</strong></p>\n",
		},
		{
			in:   "<img src='big_brandon.jpg'/>",
			want: "<p><img src=\"big_brandon.jpg\"/></p>\n",
		},
		{
			in:   "<script> console.log('xss'); </script>",
			want: "<p></p>\n",
		},
	}

	s := newMDServer()
	for _, tcase := range tests {
		req := &pb.MDRequest{MdBody: tcase.in}

		r, err := s.MarkdownToHTML(context.Background(), req)
		if err != nil {
			t.Fatalf("s.MarkdownToHTML(%v), unexpected error: %v", tcase.in, err)
		}

		if r.HtmlBody != tcase.want {
			t.Fatalf("s.MarkdownToHTML(%v)\ngot: \t%#v\nwant\t%#v",
				tcase.in, r.HtmlBody, tcase.want)
		}

	}
}
