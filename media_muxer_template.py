#!/usr/bin/env python3
"""
Generic template for tagging and muxing TV episode media files.

Copy this file and update the configuration values for each show.
This template is designed to be reusable for future projects.
"""

import argparse
import os
import time
from pathlib import Path

import tmdbsimple as tmdb
from pymkv import MKVFile, MKVTrack

DEFAULT_API_KEY = "YOUR_TMDB_API_KEY"
DEFAULT_MAX_RETRIES = 10


def load_env_file(env_path: str | Path | None = None):
    """Load key/value pairs from a .env file if it exists."""
    resolved_path = Path(env_path) if env_path else Path(__file__).with_name(".env")
    values = {}

    if not resolved_path.exists():
        return values

    for raw_line in resolved_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


def get_api_key(env_file: str | Path | None = None, default_key: str = DEFAULT_API_KEY):
    """Get the API key from environment variables first, then .env file, then fallback default."""
    key = os.environ.get("TMDB_API_KEY")
    if key:
        return key

    env_values = load_env_file(env_file)
    key = env_values.get("TMDB_API_KEY")
    if key:
        return key

    return default_key


def normalize_names(value):
    """Accept a single string or list and return a normalized list of names."""
    if value is None:
        return []
    if isinstance(value, str):
        return [name.strip() for name in value.split(",") if name.strip()]
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def get_movie_metadata(movie_name: str, api_key: str | None = None, max_retries: int = DEFAULT_MAX_RETRIES):
    """Return basic metadata for a movie from TMDb."""
    api_key = api_key or get_api_key()
    tmdb.API_KEY = api_key

    for attempt in range(max_retries):
        try:
            search = tmdb.Search()
            response = search.movie(query=movie_name)
            results = response.get("results") or []

            if not results:
                raise ValueError(f"Movie '{movie_name}' not found on TMDb.")

            movie_result = results[0]
            movie_id = movie_result["id"]
            movie = tmdb.Movies(movie_id)
            movie_data = movie.info()
            title = movie_data.get("title") or movie_data.get("original_title") or movie_name

            return {
                "title": title,
                "release_date": movie_data.get("release_date"),
                "filename": f"{title}.mkv",
            }

        except Exception as exc:
            if attempt < max_retries - 1:
                delay = 2 ** attempt
                print(f"TMDb movie lookup failed: {exc}. Retrying in {delay} seconds (attempt {attempt + 2}/{max_retries}).")
                time.sleep(delay)
            else:
                print(f"Final TMDb movie error after {max_retries} attempts: {exc}")
                return None

    return None


def get_episode_metadata(series_name: str, season_num: int, episode_num: int, api_key: str | None = None, max_retries: int = DEFAULT_MAX_RETRIES):
    """Return episode metadata from TMDb for a given TV series and episode."""
    api_key = api_key or get_api_key()
    tmdb.API_KEY = api_key
    series_id = None
    series_title = None

    for attempt in range(max_retries):
        try:
            if series_id is None:
                search = tmdb.Search()
                response = search.tv(query=series_name)
                results = response.get("results") or []

                if not results:
                    raise ValueError(f"Series '{series_name}' not found on TMDb.")

                main_result = results[0]
                series_id = main_result["id"]
                series_title = main_result.get("name") or main_result.get("original_name") or series_name

            episode = tmdb.TV_Episodes(series_id, season_num, episode_num)
            episode_data = episode.info()
            episode_title = episode_data.get("name")

            if not episode_title:
                raise ValueError(f"Episode S{season_num}E{episode_num} is missing a title on TMDb.")

            return {
                "series_title": series_title,
                "episode_title": episode_title,
                "season_number": season_num,
                "episode_number": episode_num,
                "filename": f"{series_title} - S{season_num:02d}E{episode_num:02d} - {episode_title}.mkv",
            }

        except Exception as exc:
            if attempt < max_retries - 1:
                delay = 2 ** attempt
                print(f"TMDb request failed: {exc}. Retrying in {delay} seconds (attempt {attempt + 2}/{max_retries}).")
                time.sleep(delay)
            else:
                print(f"Final TMDb error after {max_retries} attempts: {exc}")
                return None

    return None


def find_tracks_by_type(mkv, track_type: str):
    """Return all tracks of a given type."""
    return [track for track in mkv.tracks if track.track_type == track_type]


def update_track_properties(track, *, track_name: str, language: str, default_track: bool = True, forced_track: bool = False):
    """Apply common track metadata updates."""
    track.track_name = track_name
    track.language = language
    track.default_track = default_track
    track.forced_track = forced_track


def configure_video_tracks(mkv, video_name: str):
    """Rename video tracks and keep them default."""
    video_tracks = find_tracks_by_type(mkv, "video")
    if not video_tracks:
        raise ValueError("No video track found in the file.")

    for index, track in enumerate(video_tracks):
        name = video_name if index == 0 else f"{video_name} {index + 1}"
        update_track_properties(track, track_name=name, language="und", default_track=True, forced_track=False)


def configure_audio_tracks(mkv, audio_names, preferred_language: str = "eng"):
    """Rename audio tracks and support multiple audio tracks (2 or 3+)."""
    audio_tracks = find_tracks_by_type(mkv, "audio")
    if not audio_tracks:
        raise ValueError("No audio track found in the file.")

    names = normalize_names(audio_names)
    if not names:
        names = [f"Audio {index + 1}" for index in range(len(audio_tracks))]

    for index, track in enumerate(audio_tracks):
        track_name = names[index] if index < len(names) else f"Audio {index + 1}"
        language = preferred_language if index == 0 else "und"
        default_track = index == 0
        update_track_properties(track, track_name=track_name, language=language, default_track=default_track, forced_track=False)


def configure_subtitle_tracks(mkv, subtitle_names, preferred_language: str = "eng"):
    """Rename subtitle tracks and allow multiple subtitle tracks."""
    subtitle_tracks = find_tracks_by_type(mkv, "subtitles")
    if not subtitle_tracks:
        return False

    names = normalize_names(subtitle_names)
    if not names:
        names = [f"Subtitle {index + 1}" for index in range(len(subtitle_tracks))]

    for index, track in enumerate(subtitle_tracks):
        track_name = names[index] if index < len(names) else f"Subtitle {index + 1}"
        language = preferred_language if index == 0 else "und"
        default_track = index == 0
        update_track_properties(track, track_name=track_name, language=language, default_track=default_track, forced_track=False)
    return True


def add_subtitle_track_from_srt(mkv, subtitle_path: Path, subtitle_name: str, language: str = "eng"):
    """Add a subtitle track from an .srt file to the MKV container."""
    if not subtitle_path.exists():
        raise FileNotFoundError(f"Subtitle file not found: {subtitle_path}")

    subtitle = MKVTrack(str(subtitle_path))
    subtitle.track_name = subtitle_name
    subtitle.language = language
    subtitle.default_track = True
    subtitle.forced_track = False
    mkv.add_track(subtitle)
    return subtitle


def wire_media_tracks(mkv, *, video_name: str, audio_names, subtitle_names, preferred_language: str = "eng"):
    """Apply track metadata for files with one video, 2-3 audio tracks, and multiple subtitle tracks."""
    configure_video_tracks(mkv, video_name)
    configure_audio_tracks(mkv, audio_names, preferred_language=preferred_language)
    configure_subtitle_tracks(mkv, subtitle_names, preferred_language=preferred_language)


def process_single_episode(
    source_file: Path,
    *,
    series_name: str,
    season_num: int,
    episode_num: int,
    video_name: str,
    audio_names,
    subtitle_names,
    api_key: str = DEFAULT_API_KEY,
    preferred_language: str = "eng",
    output_dir: Path | None = None,
):
    """Process a single episode and support multiple audio/subtitle tracks."""
    if not source_file.exists():
        raise FileNotFoundError(f"Input file not found: {source_file}")

    mkv = MKVFile(str(source_file))
    wire_media_tracks(mkv, video_name=video_name, audio_names=audio_names, subtitle_names=subtitle_names, preferred_language=preferred_language)

    metadata = get_episode_metadata(series_name, season_num, episode_num, api_key=api_key)
    if metadata is None:
        raise RuntimeError(f"Could not fetch metadata for S{season_num}E{episode_num}.")

    mkv.title = metadata["episode_title"]

    if output_dir is None:
        output_dir = source_file.parent

    output_path = output_dir / f"S{season_num:02d}E{episode_num:02d}.mkv"
    mkv.mux(str(output_path))
    print(f"Created: {output_path}")
    return output_path


def process_movie(
    source_file: Path,
    *,
    movie_name: str,
    video_name: str,
    audio_names,
    subtitle_names,
    api_key: str = DEFAULT_API_KEY,
    preferred_language: str = "eng",
    output_dir: Path | None = None,
):
    """Process a single movie and support multiple audio/subtitle tracks."""
    if not source_file.exists():
        raise FileNotFoundError(f"Input file not found: {source_file}")

    mkv = MKVFile(str(source_file))
    wire_media_tracks(mkv, video_name=video_name, audio_names=audio_names, subtitle_names=subtitle_names, preferred_language=preferred_language)

    metadata = get_movie_metadata(movie_name, api_key=api_key)
    if metadata is None:
        raise RuntimeError(f"Could not fetch metadata for movie '{movie_name}'.")

    mkv.title = metadata["title"]

    if output_dir is None:
        output_dir = source_file.parent

    output_path = output_dir / f"{metadata['title']}.mkv"
    mkv.mux(str(output_path))
    print(f"Created: {output_path}")
    return output_path


def process_season(
    folder: Path,
    *,
    series_name: str,
    season_num: int,
    episode_start: int,
    episode_end: int,
    file_pattern: str,
    video_name: str,
    audio_names,
    subtitle_names,
    api_key: str = DEFAULT_API_KEY,
    input_extension: str = ".mkv",
    output_extension: str = ".mkv",
    preferred_language: str = "eng",
):
    """Process a range of episodes using a predictable pattern in a folder."""
    for episode_num in range(episode_start, episode_end + 1):
        file_name = file_pattern.format(season=season_num, episode=episode_num)
        source_file = folder / f"{file_name}{input_extension}"

        if not source_file.exists():
            print(f"Skipping missing file: {source_file}")
            continue

        print(f"\nProcessing: {source_file.name}")
        process_single_episode(
            source_file,
            series_name=series_name,
            season_num=season_num,
            episode_num=episode_num,
            video_name=video_name,
            audio_names=audio_names,
            subtitle_names=subtitle_names,
            api_key=api_key,
            preferred_language=preferred_language,
            output_dir=folder,
        )

        output_file = folder / f"S{season_num:02d}E{episode_num:02d}{output_extension}"
        print(f"Completed episode {episode_num}: {output_file.name}")


def parse_args():
    parser = argparse.ArgumentParser(description="Template for TMDb metadata and track tagging of TV episodes or movies.")
    parser.add_argument("--media-type", choices=["series", "movie"], default="series")
    parser.add_argument("--series-name", default="Your Show Name")
    parser.add_argument("--movie-name", default="Your Movie Name")
    parser.add_argument("--season", type=int, default=1)
    parser.add_argument("--episode-start", type=int, default=1)
    parser.add_argument("--episode-end", type=int, default=1)
    parser.add_argument("--folder", default="/mnt/hdd2/Downloads/YourShow/Season 1")
    parser.add_argument("--file-pattern", default="Your Show S{season:02d}E{episode:02d}")
    parser.add_argument("--video-name", default="H.264 1080p")
    parser.add_argument("--audio-names", default="English Audio, Commentary Audio")
    parser.add_argument("--subtitle-names", default="English Subtitle, Spanish Subtitle")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--input-extension", default=".mkv")
    parser.add_argument("--preferred-language", default="eng")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    resolved_api_key = args.api_key or get_api_key()

    if args.media_type == "movie":
        process_movie(
            Path(args.folder),
            movie_name=args.movie_name,
            video_name=args.video_name,
            audio_names=normalize_names(args.audio_names),
            subtitle_names=normalize_names(args.subtitle_names),
            api_key=resolved_api_key,
            preferred_language=args.preferred_language,
            output_dir=Path(args.folder),
        )
    else:
        process_season(
            Path(args.folder),
            series_name=args.series_name,
            season_num=args.season,
            episode_start=args.episode_start,
            episode_end=args.episode_end,
            file_pattern=args.file_pattern,
            video_name=args.video_name,
            audio_names=normalize_names(args.audio_names),
            subtitle_names=normalize_names(args.subtitle_names),
            api_key=resolved_api_key,
            input_extension=args.input_extension,
            output_extension=args.input_extension,
            preferred_language=args.preferred_language,
        )
