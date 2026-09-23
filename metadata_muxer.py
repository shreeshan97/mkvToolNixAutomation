#  $env:Path += ";C:\Program Files\MKVToolNix"

import tmdbsimple as tmdb
import time
from pymkv import MKVFile, MKVTrack

API_KEY = "API_KEY"  # Replace with your actual TMDb API key
MAX_RETRIES = 10

series_name = 'Friends'
season_num = 10
episode_num = 1
episode_max = 32
file_name = ''
file_path = f'/mnt/hdd2/Downloads/{series_name}/Season {season_num}'

video_name = 'H.264 1080p'
audio_name = 'English Audio'
subtitle_name = 'English Subtitle'

def get_episode_metadata(series_name, season_num, episode_num):
    """
    Connects to TMDb, searches for the series, and retrieves specific episode details with retries.
    """
    tmdb.API_KEY = API_KEY
    series_title = None

    for attempt in range(MAX_RETRIES):
        try:
            if attempt == 0:
                 print(f"Connecting to TMDb with API Key...")
            
            # 1. Search for the series (Only search on the first attempt if series_title is unknown)
            if series_title is None:
                search = tmdb.Search()
                response = search.tv(query=series_name)
                
                if not response['results']:
                    # This is a permanent error, no need to retry
                    print(f"Error: Series '{series_name}' not found on TMDb.")
                    return None
                
                main_series_result = response['results'][0]
                series_id = main_series_result['id']
                series_title = main_series_result['name']
                print(f"Found Series: {series_title} (ID: {series_id})")

            # 2. Get specific episode details
            # Directly instantiate the TV_Episode object (correct class name is assumed to be Tv_Episode)
            episode = tmdb.TV_Episodes(series_id, season_num, episode_num)
            episode_data = episode.info()
            
            episode_title = episode_data.get('name')
            
            if not episode_title:
                 # This is a permanent data error, no need to retry
                 print(f"Error: Episode S{season_num}E{episode_num} not found on TMDb or is missing a title.")
                 return None

            # 3. Return collected metadata on success
            return {
                'series_title': series_title,
                'episode_title': episode_title,
                'season_number': season_num,
                'episode_number': episode_num,
                'filename': f"{series_title} - S{season_num:02}E{episode_num:02} - {episode_title}.mkv"
            }

        except Exception as e:
            # Check if this is the last attempt
            if attempt < MAX_RETRIES - 1:
                # Calculate delay
                delay = 2 * attempt
                print(f"Connection failed: {e}. Retrying in {delay} seconds (Attempt {attempt + 2}/{MAX_RETRIES}).")
                time.sleep(delay)
            else:
                # Max retries reached
                print(f"An unexpected error occurred during TMDb query after {MAX_RETRIES} attempts: {e}")
                return None

for episode_num in range(episode_num, episode_max + 1):
    
    file_name = f"{series_name} S{season_num:02}E{episode_num:02}"
    print(f"\nProcessing files: {file_name}")
    try:
        mkv = MKVFile(f'{file_path}/{file_name}.mkv')
    except FileNotFoundError:
        print("\n\nEnd of files\n\n")
        exit()

    i = 0
    # ---- EDIT TRACK 0 (Video) ----
    video = mkv.tracks[i]
    video.track_name = video_name
    video.language = "und"
    video.default_track = True
    video.forced_track = False

    i += 1
    # ---- EDIT TRACK 1 (Audio) ----
    audio = mkv.tracks[i]
    audio.track_name = audio_name
    audio.language = "eng"
    audio.default_track = True
    audio.forced_track = False

    i += 1
    # ---- EDIT SUBTITLE TRACK ----
    for j in range(i, len(mkv.tracks)):
        subtitle = mkv.tracks[i]
        if subtitle.track_type == 'subtitles':
            break
        else:
            i += 1
    if subtitle.language == 'eng':
        subtitle.track_name = subtitle_name
        subtitle.default_track = True
        subtitle.forced_track = False
    else:
        print(f"No English subtitle track found for {file_name}.")
        exit()

    i += 1
    # ---- REMOVE NON-ENGLISH SUBTITLE TRACKS ----
    try:
        for j in range(i, len(mkv.tracks)):
            if mkv.tracks[i].language != 'eng':
                mkv.remove_track(i)
            else:
                i += 1
    except Exception as e:
        pass

    # ---- SET METADATA ----
    metadata = get_episode_metadata(series_name, season_num, episode_num)
    mkv.title = metadata['episode_title']
    # mkv.title = "TThe One in Barbados (1)"
    print(f"\n{file_name} {mkv.title}\n")

    try:
        mkv.mux(f'{file_path}/S{season_num:02}E{episode_num:02}.mkv')
        

    except Exception as e:
        pass

    print(f"\nS{season_num:02}E{episode_num:02}.mkv created successfully.\n\n")
