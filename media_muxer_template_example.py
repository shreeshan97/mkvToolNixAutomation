#!/usr/bin/env python3
"""Example usage of the reusable media muxer template."""

from pathlib import Path

from media_muxer_template import process_movie, process_season


if __name__ == "__main__":
    # Example 1: TV series with multiple audio tracks and subtitles
    season_folder = Path("/mnt/hdd2/Downloads/Friends/Season 10")

    process_season(
        season_folder,
        series_name="Friends",
        season_num=10,
        episode_start=1,
        episode_end=2,
        file_pattern="Friends S{season:02d}E{episode:02d}",
        video_name="H.264 1080p",
        audio_names=["English Audio", "Commentary Audio", "Spanish Audio"],
        subtitle_names=["English Subtitle", "Spanish Subtitle", "French Subtitle"],
        api_key="YOUR_TMDB_API_KEY",
        input_extension=".mkv",
        output_extension=".mkv",
        preferred_language="eng",
    )

    # Example 2: Movie with multiple audio tracks and subtitles
    movie_file = Path("/mnt/hdd2/Downloads/Movies/Inception.mkv")

    process_movie(
        movie_file,
        movie_name="Inception",
        video_name="H.264 1080p",
        audio_names=["English Audio", "Russian Audio", "French Audio"],
        subtitle_names=["English Subtitle", "Russian Subtitle", "French Subtitle"],
        api_key="YOUR_TMDB_API_KEY",
        preferred_language="eng",
        output_dir=movie_file.parent,
    )
