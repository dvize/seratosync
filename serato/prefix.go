package serato

import (
	"strings"
)

// CleanPath prepares a path for comparison by normalizing slashes and removing the drive letter.
func CleanPath(path string) string {
	p := strings.ReplaceAll(path, "\\", "/")
	if len(p) >= 2 && p[1] == ':' {
		p = p[2:] // Remove C:
	}
	return strings.Trim(p, "/")
}

