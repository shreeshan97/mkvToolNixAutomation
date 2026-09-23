# mkvToolNixAutomation

Python scripts for adding TMDb titles and consistent track metadata to TV episodes and movies using MKVToolNix.

## Setup

Create and activate a virtual environment, then install the Python dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install tmdbsimple pymkv
```

MKVToolNix must also be installed and available on `PATH` so `pymkv` can run `mkvmerge`.

Create `.env` from `.env.example` and add the TMDb API key:

```env
TMDB_API_KEY=your_tmdb_api_key_here
```

`.env` is ignored by Git and must not be committed.

## Template

The main reusable script is `media_muxer_template.py`. It supports:

- TV seasons and individual movies
- multiple audio tracks, including two or three tracks
- multiple subtitle tracks
- TMDb metadata lookup with retries
- configurable track names and languages

### TV series

```bash
python media_muxer_template.py \
	--media-type series \
	--series-name "Friends" \
	--season 10 \
	--episode-start 1 \
	--episode-end 32 \
	--folder "/mnt/hdd2/Downloads/Friends/Season 10" \
	--file-pattern "Friends S{season:02d}E{episode:02d}" \
	--audio-names "English Audio,Commentary Audio,Spanish Audio" \
	--subtitle-names "English Subtitle,Spanish Subtitle,French Subtitle"
```

### Movie

```bash
python media_muxer_template.py \
	--media-type movie \
	--movie-name "Inception" \
	--folder "/mnt/hdd2/Downloads/Movies/Inception.mkv" \
	--audio-names "English Audio,Russian Audio,French Audio" \
	--subtitle-names "English Subtitle,Russian Subtitle,French Subtitle"
```

The comma-separated names are applied in track order. The first audio and subtitle track is marked as the default track.

## Python usage

See `media_muxer_template_example.py` for calls to `process_season(...)` and `process_movie(...)` using lists of track names.

## Input and output

For a TV season, input files must match the configured pattern and extension, for example:

```text
Friends S10E01.mkv
Friends S10E02.mkv
```

Processed episodes are written as `S10E01.mkv`, `S10E02.mkv`, and so on. Movie output is written using the TMDb movie title.

The original scripts are preserved in Git history; new work should generally start from `media_muxer_template.py`.
