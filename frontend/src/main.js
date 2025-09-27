import { GetConfig, SaveConfig, BrowseForDirectory, SyncLibrary, GenerateReport, CleanDatabase } from '../wailsjs/go/main/App';
import { EventsOn } from '../wailsjs/runtime';

document.addEventListener('DOMContentLoaded', () => {
    const seratoDbPathInput = document.getElementById('serato-db-path');
    const musicLibraryPathInput = document.getElementById('music-library-path');
    const browseSeratoDbBtn = document.getElementById('browse-serato-db');
    const browseMusicLibraryBtn = document.getElementById('browse-music-library');
    const saveConfigBtn = document.getElementById('save-config');
    const syncLibraryBtn = document.getElementById('sync-library');
    const generateReportBtn = document.getElementById('generate-report');
    const cleanDatabaseBtn = document.getElementById('clean-database');
    const logsDiv = document.getElementById('logs');

    // Load initial config
    GetConfig().then(config => {
        seratoDbPathInput.value = config.serato_db_path;
        musicLibraryPathInput.value = config.music_library_path;
    });

    // Log messages
    EventsOn('log', message => {
        const p = document.createElement('p');
        p.textContent = message;
        logsDiv.appendChild(p);
        logsDiv.scrollTop = logsDiv.scrollHeight;
    });

    // Button listeners
    browseSeratoDbBtn.addEventListener('click', () => {
        BrowseForDirectory('Select Serato Database Directory').then(path => {
            if (path) {
                seratoDbPathInput.value = path;
            }
        });
    });

    browseMusicLibraryBtn.addEventListener('click', () => {
        BrowseForDirectory('Select Music Library Directory').then(path => {
            if (path) {
                musicLibraryPathInput.value = path;
            }
        });
    });

    saveConfigBtn.addEventListener('click', () => {
        const config = {
            serato_db_path: seratoDbPathInput.value,
            music_library_path: musicLibraryPathInput.value,
        };
        SaveConfig(config).then(() => {
            // Log or show notification
        });
    });

    syncLibraryBtn.addEventListener('click', () => {
        SyncLibrary();
    });

    generateReportBtn.addEventListener('click', () => {
        GenerateReport();
    });

    cleanDatabaseBtn.addEventListener('click', () => {
        CleanDatabase();
    });
});