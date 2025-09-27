package serato

import (
	"fmt"
	"io"
	"os"
	"strings"
	"time"
)

// CleanupStats holds the statistics of the database cleanup operation.
type CleanupStats struct {
	OriginalCount     int `json:"original_count"`
	RemovedNoPath     int `json:"removed_no_path"`
	RemovedNoMetadata int `json:"removed_no_metadata"`
	RemovedDuplicates int `json:"removed_duplicates"`
	RemovedCorrupted  int `json:"removed_corrupted"`
	FinalCount        int `json:"final_count"`
}

// CleanDatabaseRecords cleans database records by removing corrupted entries and duplicates.
func CleanDatabaseRecords(records []Record, removeDuplicates, requireMetadata bool) ([]Record, CleanupStats) {
	stats := CleanupStats{OriginalCount: len(records)}
	var cleanedRecords []Record
	seenPaths := make(map[string]struct{})

	for _, record := range records {
		pfil, ok := record["pfil"].(string)
		if !ok || strings.TrimSpace(pfil) == "" {
			stats.RemovedNoPath++
			continue
		}

		if len(pfil) < 3 || strings.Contains(pfil, "\x00") {
			stats.RemovedCorrupted++
			continue
		}

		if requireMetadata {
			title, _ := record["ttit"].(string)
			artist, _ := record["tart"].(string)
			album, _ := record["talb"].(string)
			if strings.TrimSpace(title) == "" && strings.TrimSpace(artist) == "" && strings.TrimSpace(album) == "" {
				stats.RemovedNoMetadata++
				continue
			}
		}

		if removeDuplicates {
			normalizedPath := strings.ToLower(strings.ReplaceAll(pfil, "\\", "/"))
			if _, seen := seenPaths[normalizedPath]; seen {
				stats.RemovedDuplicates++
				continue
			}
			seenPaths[normalizedPath] = struct{}{}
		}

		cleanedRecords = append(cleanedRecords, record)
	}

	stats.FinalCount = len(cleanedRecords)
	return cleanedRecords, stats
}

// BackupDatabase creates a backup of the database file.
func BackupDatabase(dbPath string) (string, error) {
	timestamp := time.Now().Unix()
	backupPath := fmt.Sprintf("%s.backup.%d", dbPath, timestamp)

	source, err := os.Open(dbPath)
	if err != nil {
		return "", err
	}
	defer source.Close()

	destination, err := os.Create(backupPath)
	if err != nil {
		return "", err
	}
	defer destination.Close()

	_, err = io.Copy(destination, source)
	if err != nil {
		return "", err
	}

	return backupPath, nil
}
