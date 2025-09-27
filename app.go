package main

import (
	"context"
	"fmt"
	"path/filepath"

	"seratosync-go/config"
	"seratosync-go/library"
	"seratosync-go/serato"

	"github.com/wailsapp/wails/v2/pkg/runtime"
)

// App struct
type App struct {
	ctx        context.Context
	configPath string
	config     *config.Config
}

// NewApp creates a new App application struct
func NewApp() *App {
	return &App{}
}

// startup is called when the app starts. The context is saved
// so we can call the runtime methods
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	a.logMessage("Application starting up...")

	// Load config
	configPath, err := config.GetDefaultConfigPath()
	if err != nil {
		a.logMessage(fmt.Sprintf("Error getting default config path: %v", err))
		return
	}
	a.configPath = configPath
	a.logMessage(fmt.Sprintf("Using config file at: %s", configPath))

	cfg, err := config.LoadConfig(configPath)
	if err != nil {
		a.logMessage(fmt.Sprintf("Error loading config: %v", err))
		return
	}
	a.config = cfg
	a.logMessage(fmt.Sprintf("Config loaded: Serato DB Path='%s', Music Library Path='%s'", cfg.SeratoDBPath, cfg.MusicLibraryPath))
}

// GetConfig returns the current configuration.
func (a *App) GetConfig() *config.Config {
	return a.config
}

// SaveConfig saves the configuration.
func (a *App) SaveConfig(cfg *config.Config) error {
	a.config = cfg
	return config.SaveConfig(a.configPath, cfg)
}

// BrowseForDirectory opens a dialog to browse for a directory.
func (a *App) BrowseForDirectory(dialogTitle string) (string, error) {
	return runtime.OpenDirectoryDialog(a.ctx, runtime.OpenDialogOptions{
		Title: dialogTitle,
	})
}

// SyncLibrary performs the library synchronization.
func (a *App) SyncLibrary() (string, error) {
	a.logMessage("Starting library sync...")

	// --- Stats counters ---

	cratesWritten := 0
	tracksWritten := 0
	tracksAddedToDb := 0

	// 1. Read config
	if a.config.SeratoDBPath == "" || a.config.MusicLibraryPath == "" {
		a.logMessage("Error: Serato DB path or Music Library path not set.")
		return "", fmt.Errorf("paths not set")
	}

	// 2. Scan library
	a.logMessage(fmt.Sprintf("Scanning music library at %s...", a.config.MusicLibraryPath))
	libraryMap, err := library.ScanLibrary(a.config.MusicLibraryPath)
	if err != nil {
		a.logMessage(fmt.Sprintf("Error scanning library: %v", err))
		return "", err
	}
	numDirs, numFiles := library.GetLibraryStats(libraryMap)
	a.logMessage(fmt.Sprintf("Found %d directories and %d audio files.", numDirs, numFiles))

	// Log first 5 files found
	filesLogged := 0
	for _, files := range libraryMap {
		if filesLogged >= 5 {
			break
		}
		for _, file := range files {
			if filesLogged >= 5 {
				break
			}
			a.logMessage(fmt.Sprintf("  - Found library file: %s", file))
			filesLogged++
		}
	}

	// 3. Read Serato database
	dbPath := filepath.Join(a.config.SeratoDBPath, "database V2")
	a.logMessage(fmt.Sprintf("Reading Serato database at %s...", dbPath))
	existingRecords, pfilSet, libraryPrefix, err := serato.ReadDatabaseV2(dbPath, a.config.MusicLibraryPath)
	if err != nil {
		a.logMessage(fmt.Sprintf("Error reading database: %v", err))
		return "", err
	}
	a.logMessage(fmt.Sprintf("Found %d tracks in the database for comparison.", len(pfilSet)))

	// Log first 5 tracks found
	tracksLogged := 0
	for pfil := range pfilSet {
		if tracksLogged >= 5 {
			break
		}
		a.logMessage(fmt.Sprintf("  - Found DB track for comparison: %s", pfil))
		tracksLogged++
	}

	a.logMessage(fmt.Sprintf("Using prefix from library path: %s", libraryPrefix))

	// 4. Detect new tracks by comparing relative paths
	var relativeTrackPaths []string
	for _, files := range libraryMap {
		relativeTrackPaths = append(relativeTrackPaths, files...)
	}

	newRelativePaths := library.DetectNewTracks(relativeTrackPaths, pfilSet)
	a.logMessage(fmt.Sprintf("Found %d new tracks.", len(newRelativePaths)))

	// Build set of affected ptrks (full paths of new tracks)
	affectedPtrks := make(map[string]struct{})
	for _, relPfil := range newRelativePaths {
		fullPfil := serato.BuildPtrk(libraryPrefix, relPfil)
		affectedPtrks[fullPfil] = struct{}{}
	}

	// 5. Build crate plans (crates need full paths)
	cratePlans := library.BuildCratePlans(libraryMap, libraryPrefix, a.config.SeratoDBPath)

	// 6. Write crate files only for crates containing affected tracks
	a.logMessage("Writing crate files...")
	for _, plan := range cratePlans {
		// Check if this crate contains any affected tracks
		hasAffected := false
		for _, ptrk := range plan.TrackPaths {
			if _, ok := affectedPtrks[ptrk]; ok {
				hasAffected = true
				break
			}
		}
		if !hasAffected {
			continue
		}

		err := serato.WriteCrateFile(plan.CratePath, plan.TrackPaths)
		if err != nil {
			a.logMessage(fmt.Sprintf("Error writing crate file %s: %v", plan.CratePath, err))
		} else {
			a.logMessage(fmt.Sprintf("Wrote crate file %s with %d tracks.", filepath.Base(plan.CratePath), len(plan.TrackPaths)))
			cratesWritten++
			tracksWritten += len(plan.TrackPaths)
		}
	}

	// 7. Add new tracks to database
	if len(newRelativePaths) > 0 {
		a.logMessage(fmt.Sprintf("Adding %d new tracks to the database...", len(newRelativePaths)))
		var newRecords []serato.Record
		for _, relPfil := range newRelativePaths {
			// Construct the full path for the database record
			fullPfil := serato.BuildPtrk(libraryPrefix, relPfil)
			newRecord := serato.Record{"pfil": fullPfil}
			newRecords = append(newRecords, newRecord)
		}

		allRecords := append(existingRecords, newRecords...)

		// Backup database before writing
		backupPath, err := serato.BackupDatabase(dbPath)
		if err != nil {
			a.logMessage(fmt.Sprintf("Error creating database backup: %v", err))
		} else {
			a.logMessage(fmt.Sprintf("Database backup created at %s", backupPath))
		}

		err = serato.WriteDatabaseV2Records(dbPath, allRecords)
		if err != nil {
			a.logMessage(fmt.Sprintf("Error writing updated database: %v", err))
		} else {
			tracksAddedToDb = len(newRelativePaths)
			a.logMessage("Successfully updated database with new tracks.")
		}
	}

	// --- Final Summary ---
	summary := "Sync Complete!"
	a.logMessage("--------------------")
	a.logMessage("SYNC SUMMARY")
	a.logMessage("--------------------")
	a.logMessage(fmt.Sprintf("Music Library Files Scanned: %d", numFiles))
	a.logMessage(fmt.Sprintf("Serato Database Tracks Before Sync: %d", len(existingRecords)))
	a.logMessage(fmt.Sprintf("New Tracks Detected: %d", len(newRelativePaths)))
	a.logMessage(fmt.Sprintf("Tracks Added to Database: %d", tracksAddedToDb))
	a.logMessage(fmt.Sprintf("Total Tracks in Database After Sync: %d", len(existingRecords)+tracksAddedToDb))
	a.logMessage(fmt.Sprintf("Crate Files Written/Updated: %d", cratesWritten))
	a.logMessage(fmt.Sprintf("Total Tracks Written to Crates: %d", tracksWritten))
	a.logMessage("--------------------")

	return summary, nil
}

func (a *App) logMessage(message string) {
	runtime.EventsEmit(a.ctx, "log", message)
}

// GenerateReport generates a database report.
func (a *App) GenerateReport() (string, error) {
	a.logMessage("Generating database report...")

	if a.config.SeratoDBPath == "" {
		a.logMessage("Error: Serato DB path not set.")
		return "", fmt.Errorf("path not set")
	}

	dbPath := filepath.Join(a.config.SeratoDBPath, "database V2")
	records, _, _, err := serato.ReadDatabaseV2(dbPath, "")
	if err != nil {
		a.logMessage(fmt.Sprintf("Error reading database: %v", err))
		return "", err
	}

	report := fmt.Sprintf("Database Report:\n- Total tracks: %d", len(records))
	a.logMessage(report)
	return report, nil
}

// CleanDatabase cleans the database.
func (a *App) CleanDatabase() (string, error) {
	a.logMessage("Cleaning database...")

	if a.config.SeratoDBPath == "" {
		a.logMessage("Error: Serato DB path not set.")
		return "", fmt.Errorf("path not set")
	}

	dbPath := filepath.Join(a.config.SeratoDBPath, "database V2")

	// Backup database
	backupPath, err := serato.BackupDatabase(dbPath)
	if err != nil {
		a.logMessage(fmt.Sprintf("Error creating backup: %v", err))
		return "", err
	}
	a.logMessage(fmt.Sprintf("Database backup created at %s", backupPath))

	// Read records
	records, _, _, err := serato.ReadDatabaseV2(dbPath, "")
	if err != nil {
		a.logMessage(fmt.Sprintf("Error reading database: %v", err))
		return "", err
	}

	// Clean records
	cleanedRecords, stats := serato.CleanDatabaseRecords(records, true, true)

	// Write cleaned records
	err = serato.WriteDatabaseV2Records(dbPath, cleanedRecords)
	if err != nil {
		a.logMessage(fmt.Sprintf("Error writing cleaned database: %v", err))
		return "", err
	}

	result := fmt.Sprintf("Database cleanup complete.\nOriginal records: %d\nCleaned records: %d", stats.OriginalCount, stats.FinalCount)
	a.logMessage(result)
	return result, nil
}
