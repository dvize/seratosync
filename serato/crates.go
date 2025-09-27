package serato

import (
	"os"
	"path/filepath"
	"strings"

	"seratosync-go/tlv"
)

// AudioExts is a set of supported audio file extensions.
var AudioExts = map[string]struct{}{
	".mp3":  {},
	".m4a":  {},
	".aac":  {},
	".aif":  {},
	".aiff": {},
	".wav":  {},
	".flac": {},
	".ogg":  {},
}

// CrateVrsn is the version string for crate files.
const CrateVrsn = "1.0/Serato ScratchLive Crate"

// IsAudioFile checks if a path is an audio file with an allowed extension.
func IsAudioFile(path string) bool {
	ext := strings.ToLower(filepath.Ext(path))
	_, ok := AudioExts[ext]
	return ok
}

// CratePathForDir generates the crate file path for a directory.
func CratePathForDir(seratoRoot, dirRel string) string {
	subcratesDir := filepath.Join(seratoRoot, "Subcrates")
	// Join path components with '%%' for the crate filename
	crateName := strings.ReplaceAll(dirRel, string(filepath.Separator), "%%") + ".crate"
	return filepath.Join(subcratesDir, crateName)
}

// BuildPtrk builds a ptrk (track path) string for a relative file.
func BuildPtrk(prefix, relFile string) string {
	parts := []string{}
	if prefix != "" {
		parts = append(parts, prefix)
	}
	parts = append(parts, strings.Split(relFile, string(filepath.Separator))...)
	return strings.Join(parts, "/")
}

// WriteCrateFile writes a crate file with the given track paths.
func WriteCrateFile(outfile string, trackPaths []string) error {
	err := os.MkdirAll(filepath.Dir(outfile), 0755)
	if err != nil {
		return err
	}

	file, err := os.Create(outfile)
	if err != nil {
		return err
	}
	defer file.Close()

	vrsnPayload, err := tlv.EncodeU16BE(CrateVrsn)
	if err != nil {
		return err
	}
	err = tlv.WriteChunk(file, "vrsn", vrsnPayload)
	if err != nil {
		return err
	}

	for _, pathStr := range trackPaths {
		ptrkPayload, err := tlv.EncodeU16BE(pathStr)
		if err != nil {
			// Log or handle error, for now we skip the track
			continue
		}
		inner := tlv.MakeChunk("ptrk", ptrkPayload)
		err = tlv.WriteChunk(file, "otrk", inner)
		if err != nil {
			// Log or handle error
			continue
		}
	}

	return nil
}

// ReadCrateFile reads an existing crate file and extracts track paths.
func ReadCrateFile(cratePath string) ([]string, error) {
	if _, err := os.Stat(cratePath); os.IsNotExist(err) {
		return []string{}, nil
	}

	file, err := os.Open(cratePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	chunks, err := tlv.IterTLV(file)
	if err != nil {
		return nil, err
	}

	var trackPaths []string
	for _, chunk := range chunks {
		if chunk.Tag == "otrk" {
			nestedChunks, err := tlv.IterNestedTLV(chunk.Value)
			if err != nil {
				continue
			}
			for _, nestedChunk := range nestedChunks {
				if nestedChunk.Tag == "ptrk" {
					pathStr, err := tlv.DecodeU16BE(nestedChunk.Value)
					if err != nil {
						continue
					}
					trackPaths = append(trackPaths, pathStr)
				}
			}
		}
	}

	return trackPaths, nil
}
