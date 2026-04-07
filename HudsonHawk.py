import os
import random
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

# A script that scans your music library and groups by length, tags, and BPM 
# to assemble playlists that approach round minute lengths (or as close as possible) 
# for user defined lengths like 10 minutes or 25 minutes (popular lengths for pomodoro timers)

def get_song_info(file_path):
    audio = MP3(file_path)
    tags = EasyID3(file_path)
    duration = audio.info.length
    genre = tags.get('genre', ['Unknown'])[0]
    bpm = tags.get('bpm', ['0'])[0]
    return {
        'path': file_path,
        'duration': duration,
        'genre': genre,
        'bpm': float(bpm) if bpm.isdigit() else 0
    }

def scan_library(directory):
    songs = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.mp3'):
                songs.append(get_song_info(os.path.join(root, file)))
    return songs

def group_songs(songs, criteria):
    groups = {}
    for song in songs:
        key = tuple(song[c] for c in criteria)
        if key not in groups:
            groups[key] = []
        groups[key].append(song)
    return groups

def assemble_playlist(groups, target_minutes):
    target_seconds = target_minutes * 60
    best_playlist = []
    best_diff = float('inf')
    
    for group in groups.values():
        if not group:
            continue
        # Simple greedy approach: sort by duration and add until close
        group.sort(key=lambda x: x['duration'])
        current_sum = 0
        playlist = []
        for song in group:
            if current_sum + song['duration'] <= target_seconds + 60:  # Allow some overrun
                playlist.append(song)
                current_sum += song['duration']
            if abs(current_sum - target_seconds) < best_diff:
                best_playlist = playlist.copy()
                best_diff = abs(current_sum - target_seconds)
        # Could optimize further, but this is basic
    return best_playlist

if __name__ == "__main__":
    library_dir = input("Enter music library directory: ")
    target_minutes = int(input("Enter target playlist length in minutes: "))
    criteria = ['genre', 'bpm']  # Example grouping criteria
    
    songs = scan_library(library_dir)
    groups = group_songs(songs, criteria)
    playlist = assemble_playlist(groups, target_minutes)
    
    print(f"Playlist for {target_minutes} minutes:")
    total_time = 0
    for song in playlist:
        print(f"{song['path']} - {song['duration']:.2f}s")
        total_time += song['duration']
    print(f"Total time: {total_time / 60:.2f} minutes")