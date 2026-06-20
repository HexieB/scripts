"""Bulk-add audio metadata (title, artist, duration).

Behavior:
- Sets the track title from the filename (filename without extension).
- Sets the artist from a single user-supplied value (CLI arg or prompt).
- Detects the audio length and writes it to a duration tag where supported.

Usage:
  python MetaDataSet.py --dir /path/to/music --artist "Artist Name"

Notes:
- Requires the `mutagen` package: `pip install mutagen`
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

try:
	import mutagen
	from mutagen.easyid3 import EasyID3
	from mutagen.id3 import ID3, TLEN, ID3NoHeaderError
	from mutagen.flac import FLAC
	from mutagen.oggvorbis import OggVorbis
except Exception:  # pragma: no cover - helpful user message
	print("This script requires the 'mutagen' package. Install with: pip install mutagen")
	raise


SUPPORTED_EXTS = {".mp3", ".flac", ".ogg", ".m4a", ".mp4", ".wav", ".aac", ".opus"}


def get_title_from_filename(path: Path) -> str:
	return path.stem


def write_tags(path: Path, title: str, artist: str, dry_run: bool = False) -> None:
	ext = path.suffix.lower()
	audio = mutagen.File(path)
	length_seconds: Optional[float] = None
	if audio is not None and hasattr(audio, "info") and getattr(audio.info, "length", None):
		length_seconds = float(audio.info.length)

	if dry_run:
		print(f"DRY RUN: {path} -> title={title!r}, artist={artist!r}, length={length_seconds}")
		return

	# Try easy tags first (works for many formats)
	try:
		easy = mutagen.File(path, easy=True)
		if easy is None:
			easy = {}
		# Set title/artist using the common field names
		try:
			easy["title"] = [title]
			easy["artist"] = [artist]
			easy.save()
		except Exception:
			# Not all containers support easy tags; fall through to specific handlers
			pass
	except Exception:
		pass

	# Format-specific handling for duration tag
	if ext == ".mp3":
		# MP3: use ID3 and TLEN (milliseconds)
		try:
			try:
				id3 = ID3(path)
			except ID3NoHeaderError:
				id3 = ID3()
			# Ensure title and artist exist as standard frames
			if title:
				id3.add(mutagen.id3.TIT2(encoding=3, text=title))
			if artist:
				id3.add(mutagen.id3.TPE1(encoding=3, text=artist))
			if length_seconds:
				ms = str(int(round(length_seconds * 1000)))
				# TLEN expects the length in milliseconds as text
				id3.add(TLEN(encoding=3, text=ms))
			id3.save(path)
		except Exception as e:
			print(f"Warning: failed to write ID3 tags for {path}: {e}")
	elif ext == ".flac":
		try:
			fl = FLAC(path)
			fl["TITLE"] = title
			fl["ARTIST"] = artist
			if length_seconds is not None:
				fl["LENGTH"] = str(int(round(length_seconds)))
			fl.save()
		except Exception as e:
			print(f"Warning: failed to write FLAC tags for {path}: {e}")
	elif ext in {".ogg"}:
		try:
			og = OggVorbis(path)
			og["title"] = title
			og["artist"] = artist
			if length_seconds is not None:
				og["length"] = str(int(round(length_seconds)))
			og.save()
		except Exception as e:
			print(f"Warning: failed to write Ogg tags for {path}: {e}")
	else:
		# Generic attempt: mutagen's File(..., easy=True) previously saved common fields.
		# For containers that don't support tagging, mutagen will raise; we already attempted easy save.
		try:
			audio = mutagen.File(path)
			if audio is not None:
				# best-effort: set a generic "length" tag where supported
				if length_seconds is not None:
					try:
						audio.tags["LENGTH"] = str(int(round(length_seconds)))
					except Exception:
						pass
				try:
					audio.save()
				except Exception:
					pass
		except Exception:
			pass


def iter_audio_files(root: Path, recursive: bool = True):
	if not root.exists():
		return
	if recursive:
		for p in root.rglob("*"):
			if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
				yield p
	else:
		for p in root.iterdir():
			if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
				yield p


def main(argv: Optional[list[str]] = None) -> int:
	p = argparse.ArgumentParser(description="Bulk set audio metadata: title from filename, artist from input, length from file")
	p.add_argument("--dir", "-d", default=".", help="Directory to scan for audio files")
	p.add_argument("--artist", "-a", default=None, help="Artist name to set on all files")
	p.add_argument("--no-recursive", dest="recursive", action="store_false", help="Do not recurse into subdirectories")
	p.add_argument("--dry-run", action="store_true", help="Show what would be changed without writing tags")
	args = p.parse_args(argv)

	root = Path(args.dir).expanduser().resolve()
	if not root.exists():
		print(f"Error: directory does not exist: {root}")
		return 2

	artist = args.artist
	if not artist:
		try:
			artist = input("Artist name to set on all files: ").strip()
		except KeyboardInterrupt:
			print("\nAborted.")
			return 1
	if not artist:
		print("No artist provided; aborting.")
		return 3

	count = 0
	for fp in iter_audio_files(root, recursive=args.recursive):
		title = get_title_from_filename(fp)
		try:
			write_tags(fp, title, artist, dry_run=args.dry_run)
			count += 1
		except Exception as e:
			print(f"Failed processing {fp}: {e}")

	print(f"Processed {count} files under {root}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())

