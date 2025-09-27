package config

import (
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
)

// Config holds the application configuration.
type Config struct {
	SeratoDBPath      string `json:"serato_db_path"`
	MusicLibraryPath string `json:"music_library_path"`
}

// GetDefaultConfigPath returns the default configuration file path based on the OS.
func GetDefaultConfigPath() (string, error) {
	var configPath string

	// Check current working directory first
	cwd, err := os.Getwd()
	if err == nil {
		localConfig := filepath.Join(cwd, "config.json")
		if _, err := os.Stat(localConfig); err == nil {
			return localConfig, nil
		}
	}

	switch runtime.GOOS {
	case "windows":
		appdata, err := os.UserConfigDir()
		if err != nil {
			return "", err
		}
		configPath = filepath.Join(appdata, "seratosync", "config.json")
	case "darwin":
		configDir, err := os.UserHomeDir()
		if err != nil {
			return "", err
		}
		configPath = filepath.Join(configDir, "Library", "Application Support", "seratosync", "config.json")
	default: // Linux and others
		configDir, err := os.UserConfigDir()
		if err != nil {
			return "", err
		}
		configPath = filepath.Join(configDir, "seratosync", "config.json")
	}
	return configPath, nil
}

// LoadConfig loads configuration from a JSON file.
func LoadConfig(path string) (*Config, error) {
	configFile, err := os.Open(path)
	if err != nil {
		if os.IsNotExist(err) {
			return &Config{}, nil // Return empty config if file doesn't exist
		}
		return nil, err
	}
	defer configFile.Close()

	var config Config
	decoder := json.NewDecoder(configFile)
	err = decoder.Decode(&config)
	if err != nil {
		return nil, err
	}

	return &config, nil
}

// SaveConfig saves configuration to a JSON file.
func SaveConfig(path string, config *Config) error {
	// Create directory if it doesn't exist
	err := os.MkdirAll(filepath.Dir(path), 0755)
	if err != nil {
		return err
	}

	file, err := os.Create(path)
	if err != nil {
		return err
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	return encoder.Encode(config)
}
