package main

import (
	"fmt"
	"strings"
	"testing"
)

func TestParseBlacklist(t *testing.T) {
	tests := []struct {
		in  string
		out Blacklist
	}{
		{
			in:  "",
			out: map[string]struct{}{},
		},
		{
			in: "#yes\nnice\ncool\nouch\n",
			out: map[string]struct{}{
				"nice": struct{}{},
				"cool": struct{}{},
				"ouch": struct{}{},
			},
		},
		{
			in: "# YES!! \n owie \n  cool # inline dank \n\n\nouch \n",
			out: map[string]struct{}{
				"owie": struct{}{},
				"cool": struct{}{},
				"ouch": struct{}{},
			},
		},
	}

	compare := func(out Blacklist, test Blacklist) error {
		for host_out := range out {
			if _, exists := test[host_out]; !exists {
				return fmt.Errorf("%#v not in test set", host_out)
			}
		}
		for host_test := range test {
			if _, exists := out[host_test]; !exists {
				return fmt.Errorf("%#v not in output", host_test)
			}
		}
		return nil
	}

	for _, tcase := range tests {
		o := NewBlacklist(strings.NewReader(tcase.in))
		if err := compare(o, tcase.out); err != nil {
			t.Errorf("tcase: %#v: %v", tcase.in, err)
		}
	}
}
