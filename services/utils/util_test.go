package util

import "testing"

func TestParseUsername(t *testing.T) {
	tests := []struct {
		fqu      string
		username string
		host     string
		err      bool
	}{
		{
			fqu:      "foo",
			username: "foo",
		},
		{
			fqu:      "@foo",
			username: "foo",
		},
		{
			fqu:      "foo@bar",
			username: "foo",
			host:     "bar",
		},
		{
			fqu:      "@foo@bar",
			username: "foo",
			host:     "bar",
		},
		{
			fqu: "foo@bar@ton",
			err: true,
		},
	}

	for _, tcase := range tests {
		u, h, err := ParseUsername(tcase.fqu)
		if err != nil && tcase.err {
			continue
		} else if err != nil {
			t.Errorf("ParseUsername(%#v): unexpected error: %v", tcase.fqu, err)
			continue
		} else if tcase.err {
			t.Errorf("ParseUsername(%#v): want error", tcase.fqu)
			continue
		}

		if u != tcase.username || h != tcase.host {
			t.Errorf("ParseUsername(%#v) = (%#v, %#v), want (%#v, %#v)",
				tcase.fqu, u, h, tcase.username, tcase.host)
		}
	}
}
