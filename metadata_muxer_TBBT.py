#  $env:Path += ";C:\Program Files\MKVToolNix"

import tmdbsimple as tmdb
import time
from pymkv import MKVFile, MKVTrack

API_KEY = "API_KEY"  # Replace with your actual TMDb API key
MAX_RETRIES = 10

file_path = '/mnt/hdd2/Downloads/The_Big_Bang_Theory/Season 12'
series_name = 'The Big Bang Theory'
season_num = 12
episode_num = 24
episode_max = 32
file_name = ''

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
                # Calculate delay (exponential backoff: 2, 4, 8, 16, 32 seconds)
                delay = 2 ** attempt
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
        mkv = MKVFile(f'{file_path}/{file_name}.mp4')
    except FileNotFoundError:
        print("\n\nEnd of files\n\n")
        exit()

    # ---- EDIT TRACK 0 (Video) ----
    video_track = mkv.tracks[0]
    video_track.track_name = video_name
    video_track.language = "und"
    video_track.default_track = True
    video_track.forced_track = False

    # ---- EDIT TRACK 1 (Audio) ----
    audio_track = mkv.tracks[1]
    audio_track.track_name = audio_name
    audio_track.language = "eng"
    audio_track.default_track = True
    audio_track.forced_track = False

    # ---- ADD SUBTITLE TRACK ----
    subtitle = MKVTrack(f'{file_path}/{file_name}.srt')
    subtitle.track_name = subtitle_name
    subtitle.language = 'eng'
    subtitle.default_track = True
    subtitle.forced_track = False
    mkv.add_track(subtitle)

    metadata = get_episode_metadata(series_name, season_num, episode_num)
    # ---- SET METADATA ----
    mkv.title = metadata['episode_title']

    try:
        mkv.mux(f'{file_path}/S{season_num:02}E{episode_num:02}.mkv')
        

    except Exception as e:
        pass

    print(f"\nS{season_num:02}E{episode_num:02}.mkv created successfully.\n\n")
