package library

import (
	"os"
	"path/filepath"

	"seratosync-go/serato"
)

// LibraryMap is a map of relative directory paths to lists of relative file paths.
type LibraryMap map[string][]string

// ScanLibrary scans the library directory and returns a mapping of relative directories to audio files.
func ScanLibrary(libraryRoot string) (LibraryMap, error) {
	libraryMap := make(LibraryMap)

	err := filepath.Walk(libraryRoot, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() && serato.IsAudioFile(path) {
			relDir, err := filepath.Rel(libraryRoot, filepath.Dir(path))
			if err != nil {
				return err
			}
			relFile, err := filepath.Rel(libraryRoot, path)
			if err != nil {
				return err
			}
			libraryMap[relDir] = append(libraryMap[relDir], relFile)
		}
		return nil
	})

	if err != nil {
		return nil, err
	}

	return libraryMap, nil
}

// GetLibraryStats gets statistics from the library scan results.
func GetLibraryStats(libraryMap LibraryMap) (int, int) {
	numDirs := len(libraryMap)
	numFiles := 0
	for _, files := range libraryMap {
		numFiles += len(files)
	}
	return numDirs, numFiles
}

// CratePlan represents a plan to create a crate file.
type CratePlan struct {
	CratePath  string
	TrackPaths []string
}

// BuildCratePlans builds crate file plans based on library structure.
func BuildCratePlans(libraryMap LibraryMap, prefix, seratoRoot string) []CratePlan {
	var cratePlans []CratePlan

	for relDir, files := range libraryMap {
		if relDir == "." {
			continue // Skip root directory
		}

		var newPtrks []string
		for _, f := range files {
			newPtrks = append(newPtrks, serato.BuildPtrk(prefix, f))
		}

		crateFile := serato.CratePathForDir(seratoRoot, relDir)
		cratePlans = append(cratePlans, CratePlan{CratePath: crateFile, TrackPaths: newPtrks})
	}

	return cratePlans
}

// DetectNewTracks detects which tracks are new (not in existing database).
func DetectNewTracks(trackPaths []string, existingPfilSet map[string]struct{}) []string {
	var newTracks []string
	for _, p := range trackPaths {
		cleaned := serato.CleanPath(p)
		if _, ok := existingPfilSet[cleaned]; !ok {
			newTracks = append(newTracks, p)
		}
	}
	return newTracks
}
