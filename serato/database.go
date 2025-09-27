package serato

import (
	"bytes"
	"fmt"
	"os"
	"strings"

	"seratosync-go/tlv"
)

// Record represents a track record in the Serato database.
type Record map[string]interface{}

// ReadDatabaseV2 reads all track records from a Serato Database V2 file.
// It returns the records, a set of file paths with the library prefix stripped,
// the calculated library prefix, and any error that occurred.
func ReadDatabaseV2(path string, musicLibraryPath string) ([]Record, map[string]struct{}, string, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, nil, "", err
	}
	defer file.Close()

	chunks, err := tlv.IterTLV(file)
	if err != nil {
		return nil, nil, "", err
	}

	var records []Record
	originalPfilSet := make(map[string]struct{})

	for _, chunk := range chunks {
		if chunk.Tag == "otrk" {
			record, err := parseRecord(chunk.Value)
			if err != nil {
				continue
			}
			records = append(records, record)

			if pfil, ok := record["pfil"].(string); ok {
				cleanedPfil := CleanPath(pfil)
				originalPfilSet[cleanedPfil] = struct{}{}
			}
		}
	}

	// The prefix to be stripped is the user's music library path, cleaned for comparison.
	libraryPrefix := CleanPath(musicLibraryPath)
	prefixWithSlash := ""
	if libraryPrefix != "" {
		prefixWithSlash = libraryPrefix + "/"
	}

	// Strip the library prefix from all database paths for accurate comparison.
	strippedPfilSet := make(map[string]struct{})
	for pfil := range originalPfilSet {
		// Only strip the prefix if the path actually has it. Some DB entries might be from other drives.
		if libraryPrefix == "" || strings.HasPrefix(pfil, prefixWithSlash) {
			strippedPfilSet[strings.TrimPrefix(pfil, prefixWithSlash)] = struct{}{}
		} else {
			// If the path doesn't have the prefix, it's outside our target library.
			// We can't reliably match it, so we don't include it in the comparison set.
		}
	}

	return records, strippedPfilSet, libraryPrefix, nil
}

func parseRecord(data []byte) (Record, error) {
	record := make(Record)
	nestedChunks, err := tlv.IterNestedTLV(data)
	if err != nil {
		return nil, err
	}

	for _, chunk := range nestedChunks {
		switch chunk.Tag {
		case "pfil", "ttyp", "tadd", "talb", "tart", "ttit", "tgen", "tkey", "tcom", "tgrp", "tbit", "tsmp", "tbpm", "tlen", "tmod":
			cleanValue := bytes.TrimRight(chunk.Value, "\x00")
			val, err := tlv.DecodeU16BE(cleanValue)
			if err != nil {
				return nil, fmt.Errorf("failed to decode tag %s: %w", chunk.Tag, err)
			}
			record[chunk.Tag] = val
		default:
			record[chunk.Tag] = chunk.Value
		}
	}

	return record, nil
}

// WriteDatabaseV2Records writes track records back to Database V2.
func WriteDatabaseV2Records(path string, records []Record) error {
	file, err := os.Create(path)
	if err != nil {
		return err
	}
	defer file.Close()

	// Write version header
	vrsnPayload, err := tlv.EncodeU16BE("2.0/Serato Scratch LIVE Database")
	if err != nil {
		return err
	}
	err = tlv.WriteChunk(file, "vrsn", vrsnPayload)
	if err != nil {
		return err
	}

	for _, record := range records {
		var inner bytes.Buffer
		for key, value := range record {
			switch v := value.(type) {
			case string:
				payload, err := tlv.EncodeU16BE(v)
				if err != nil {
					return err
				}
				inner.Write(tlv.MakeChunk(key, payload))
			case []byte:
				inner.Write(tlv.MakeChunk(key, v))
			}
		}
		err = tlv.WriteChunk(file, "otrk", inner.Bytes())
		if err != nil {
			return err
		}
	}

	return nil
}
