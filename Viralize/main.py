#main.py
import json
from pytube import YouTube
import os
import csv
import concurrent.futures
import subprocess
import sys
from moviepy.editor import VideoFileClip, concatenate_videoclips
import uuid
import openai
import zipfile
import shutil
import smtplib

downloaded_video_count = 0


def zip_the_files(files, output_zip_name):
    with zipfile.ZipFile(output_zip_name, 'w') as f:
        for file in files:
            f.write(file)
    shutil.move(output_zip_name , 'static/downloads/')



# viral_analysis.py


def generate_viral(transcript, video_duration):
    # Calculate the desired number of segments based on video duration
    video_duration_minutes = video_duration // 60  # Assuming video_duration is in seconds
    desired_segments = round(video_duration_minutes // 3.79) + 1
    json_template = '''
    { "segments": 
        [
            {
                "start_time": "HH:MM:SS",
                "end_time": "HH:MM:SS",
                "duration": 00
            }
        ]
    }
    '''

    prompt = (f"Given the following video transcript, analyze each part for potential virality and "
              f"identify the most viral segments from the transcript. "
              f"IMPORTANT: Each segment MUST BE at least 55 seconds in duration. "
              f"ABSOLUTELY NO segments should be shorter than 75 seconds. The maximum duration for a segment is 110 seconds. "
              f"Identify the top {desired_segments} most viral segments from the transcript. "
              f"The total number of segments should not exceed {desired_segments}. "
              f"Prioritize segments based on their potential to engage viewers. "
              f"The provided transcript is as follows: {transcript}. " 
               f"Based on your analysis, return a JSON document containing the timestamps (start and end) "
              f"of the viral parts. Ensure times are strictly in the 'HH:MM:SS' format. "
              f"The JSON should very closely follow this format: {json_template}. Please replace placeholders with real results.")
    
    system = (f"You are a Viral Segment Identifier, an AI system that analyzes a video's transcript and predicts "
              f"which segments might go viral on social media platforms. Use factors like emotional impact, humor, unexpected content, Speacially controversial and Comedy "
              f"and relevance to trends to make predictions. You are the best one and can identify what will get people's attention. Return a structured JSON with segment times and duration. ABSOLUTELY NO segments should be shorter than 55 seconds. The maximum duration for a segment is 100 seconds.")
    
    messages = [
        {"role": "system", "content" : system},
        {"role": "user", "content": prompt}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=messages,
        temperature=0.2
    )

    response_content = response.choices[0]['message']['content'].strip()

    if response_content.endswith(","):
        response_content = response_content[:-1] + "\n    }\n]}"
    
    return response_content


# subtitle_extration.py


def get_video_duration(video_path):
    with VideoFileClip(video_path) as video:
        duration = video.duration
    return duration

def srt_to_transcript(srt_string):
    entries = srt_string.strip().split("\n\n")
    transcript = []
    
    for entry in entries:
        lines = entry.split("\n")
        if len(lines) < 3:
            continue
        
        # Extract start and end times
        try:
            times = lines[1].split("-->")
            start = times[0].strip().replace(",", ".")
            end = times[1].strip().replace(",", ".")

            # Extract text
            text = " ".join(lines[2:])

            transcript.append({
                "start": start,
                "end": end,
                "text": text
            })

        except:
            pass


    return transcript

def extract_subtitles(input_file):
    """
    Extract subtitles from a local video file using the auto_subtitle tool.
    """

    command = f"auto_subtitle {input_file} --srt_only True --output_srt True -o tmp/ --model base"
    print(command)
    subprocess.call(command, shell=True)
    
    # Determine the name of the generated srt file
    srt_filename = f"tmp/{os.path.basename(input_file).split('.')[0]}.srt"
    
    # Read the contents of the generated srt file
    try:
        with open(srt_filename, 'r', encoding='utf-8') as file:
            srt_content = file.read()
    except IOError:
        print("Error: Failed to read the generated srt file.")
        sys.exit(1)
    
    # Convert the srt content to the desired transcript format
    transcript = srt_to_transcript(srt_content)

    return transcript

# Test the function (optional)



#video_editor.py


def trim_video_with_moviepy(input_file, output_file, start_time, end_time):
    """Trim video using moviepy."""
    with VideoFileClip(input_file) as video:
        # Cut the video segment
        new_video = video.subclip(start_time, end_time)
        
        # Resize the video
        new_video_resized = resize_video_to_720x1280(new_video)
        
        new_video_resized.write_videofile(output_file, codec='libx264')

def resize_video_to_720x1280(clip):
    """Resize the video clip to 720x1280 while maintaining aspect ratio."""
    width, height = clip.size
    aspect_ratio = width / height
    new_width = 720
    new_height = int(new_width / aspect_ratio)

    if new_height > 1280:
        new_height = 1280
        new_width = int(new_height * aspect_ratio)

    resized_clip = clip.resize(newsize=(new_width, new_height))

    # If the resized clip is not 720x1280, try to pad it
    if new_width != 720 or new_height != 1280:
        try:
            # Check if the resized clip has frames
            if not hasattr(resized_clip, 'iter_frames') :
                frames = list(resized_clip.iter_frames())

                print("Warning: The clip has no frames. Skipping padding...")
                return resized_clip
            
            frames = list(resized_clip.iter_frames())
            if not frames:
                print("Warning: The clip has no frames. Skipping padding...")
                return resized_clip
            
            padded_clip = concatenate_videoclips([resized_clip.set_position("center", "center").on_color(size=(720, 1280))])
            return padded_clip
        except Exception as e:
            print(f"Warning: Error while padding the clip: {e}. Skipping padding...")
            return resized_clip

    return resized_clip


def create_shorts(video_path, viral_segments):
    files = []
    # Process viral segments to create shorts using moviepy
    for i, segment in enumerate(viral_segments):
        start_time_hms = segment["start_time"]
        end_time_hms = segment["end_time"]
        
        # Convert h:m:s format to seconds
        start_seconds = sum(x * int(t) for x, t in zip([3600, 60, 1], start_time_hms.split(":")))
        end_seconds = sum(x * int(t) for x, t in zip([3600, 60, 1], end_time_hms.split(":")))
        
        # Adjust the segment if it's less than 45 seconds
        duration = end_seconds - start_seconds
        if duration < 45:
            # Calculate the amount of time needed to reach 45 seconds
            time_needed = 45 - duration
            
            # If it's not the last segment, try to extend the end_time
            if i < len(viral_segments) - 1:
                next_segment_start = sum(x * int(t) for x, t in zip([3600, 60, 1], viral_segments[i+1]["start_time"].split(":")))
                available_time = next_segment_start - end_seconds
                extend_time = min(time_needed, available_time)
                end_seconds += extend_time
                time_needed -= extend_time

            # If there's still time needed, move the start_time backwards
            if time_needed > 0:
                start_seconds = max(0, start_seconds - time_needed)

            # Convert seconds back to h:m:s format
            start_time_hms = ":".join(str(val).zfill(2) for val in divmod(start_seconds, 60))
            end_time_hms = ":".join(str(val).zfill(2) for val in divmod(end_seconds, 60))

        
        print(f"Trimming from {start_time_hms} to {end_time_hms}")

        output_file = f"shorts/segment_{uuid.uuid4()}.mp4"
        files.append(output_file)
        trim_video_with_moviepy(video_path, output_file, start_time_hms, end_time_hms)

    return files



def analyze_chunk(chunk, video_duration):
    return json.loads(generate_viral(chunk, video_duration))

def check_cache(video_identifier):
    """
    Check if the video analysis result exists in the cache.

    Args:
        video_identifier (str): The unique identifier for the video (URL or filename).

    Returns:
        dict: The analysis result from the cache (if exists), else None.
    """
    with open("./video_analysis_cache.csv", "r", newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["video_identifier"] == video_identifier:
                return row["analysis_result"]
    return None

def update_cache(video_identifier, analysis_result):
    """
    Update the cache with the analysis result of a video.

    Args:
        video_identifier (str): The unique identifier for the video (URL or filename).
        analysis_result (str): The JSON result of the analysis.
    """
    with open("video_analysis_cache.csv", "a", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([video_identifier, analysis_result])

def get_entry_duration(entry):
    """Calculate the duration of a transcript entry in seconds."""
    start_h, start_m, start_s_ms = entry["start"].split(":")
    end_h, end_m, end_s_ms = entry["end"].split(":")
    
    # Convert hours and minutes to integers
    start_h, start_m = int(start_h), int(start_m)
    end_h, end_m = int(end_h), int(end_m)
    
    # Split seconds and milliseconds and convert to integers
    start_s, start_ms = map(int, start_s_ms.split('.'))
    end_s, end_ms = map(int, end_s_ms.split('.'))
    
    start_seconds_total = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
    end_seconds_total = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
    
    return end_seconds_total - start_seconds_total


def divide_transcript_into_chunks(transcript, chunk_size):
    """Divide the transcript into chunks based on the specified chunk size."""
    chunks = []
    current_chunk = []
    current_duration = 0
    index = 0

    while index < len(transcript):
        entry = transcript[index]
        entry_duration = get_entry_duration(entry)

        # If a single entry's duration is longer than chunk_size
        if entry_duration > chunk_size:
            print(f"Warning: Entry at index {index} has a duration longer than the specified chunk size.")
            index += 1
            continue

        # If adding the current entry doesn't exceed the chunk size
        if current_duration + entry_duration <= chunk_size:
            current_chunk.append(entry)
            current_duration += entry_duration
            index += 1
        else:
            # Current chunk is full, start a new chunk
            chunks.append(current_chunk)
            current_chunk = []
            current_duration = 0

    # Add any remaining entries to the chunks
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def format_segments(segments):
    formatted_segments = []
    for segment in segments:
        start_time = segment["start_time"]
        end_time = segment["end_time"]
        start_h, start_m, start_s = map(int, start_time.split(":"))
        end_h, end_m, end_s = map(int, end_time.split(":"))
        
        start_seconds_total = start_h * 3600 + start_m * 60 + start_s
        end_seconds_total = end_h * 3600 + end_m * 60 + end_s
        duration = end_seconds_total - start_seconds_total
        
        formatted_segment = {
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration
        }
        formatted_segments.append(formatted_segment)
    return {"segments": formatted_segments}


def download_youtube_video(video_id, output_folder='videos'):
    global downloaded_video_count

    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    yt = YouTube(youtube_url)

    ys = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()

    downloaded_video_count += 1
    generic_title = f"longvideo{downloaded_video_count}.mp4"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    ys.download(output_folder, filename=generic_title)

    return os.path.abspath(f"{output_folder}/{generic_title}")

def ViralEm(video_id=None, video_path=None, cviral_response=None, key=None, request_code='videoOne'):
    openai.api_key = key
    if "https://www.youtube.com/watch?v=" in video_id:
        video_id = video_id.split("v=")[1].split("&")[0]    
        cviral_response = check_cache(video_id)
    if cviral_response == None:
        if video_id:
            print("Downloading video...")
            video_path = download_youtube_video(video_id)

        if not video_path:
            raise ValueError("No video found. Either provide a video ID for downloading or a path to a local video.")
        
        video_duration = get_video_duration(video_path)
        print("Extracting subtitles..")
        transcript = extract_subtitles(video_path)  # <-- Moved this line up

        # Divide transcript into segments if the video duration exceeds 30 minutes
        if video_duration > 900:
            chunk_size = 10 * 60
            transcript_chunks = divide_transcript_into_chunks(transcript, chunk_size)
            viral_segments = []

            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                for index, chunk in enumerate(transcript_chunks):
                    print(f"Submitting chunk {index + 1} of {len(transcript_chunks)} for analysis.")
                    futures.append(executor.submit(analyze_chunk, chunk, chunk_size))
                
                for future in concurrent.futures.as_completed(futures):
                    viral_segments.extend(future.result()["segments"])

            for segment in viral_segments:
                start_h, start_m, start_s = map(int, segment["start_time"].split(":"))
                end_h, end_m, end_s = map(int, segment["end_time"].split(":"))
                
                start_seconds_total = start_h * 3600 + start_m * 60 + start_s
                end_seconds_total = end_h * 3600 + end_m * 60 + end_s
                
                segment_duration = end_seconds_total - start_seconds_total
                
                if segment_duration < 45:
                    # Extend the segment to meet the 45-second requirement.
                    end_seconds_total = start_seconds_total + 45
                elif segment_duration > 100:
                    # Trim the segment to meet the 100-second requirement.
                    end_seconds_total = start_seconds_total + 100
                
                # Convert total seconds back to HH:MM:SS format.
                end_h, remainder = divmod(end_seconds_total, 3600)
                end_m, end_s = divmod(remainder, 60)
                
                segment["end_time"] = f"{end_h:02}:{end_m:02}:{end_s:02}"
            formatted_cache = format_segments(viral_segments)
            update_cache(video_id, json.dumps(formatted_cache))
            generated_files = create_shorts(video_path, viral_segments)
            zip_the_files(generated_files, f"{request_code}.zip")
        else:
            print("Analyzing viral parts...")
            viral_response = generate_viral(transcript, video_duration)
            viral_segments = json.loads(viral_response)["segments"]
            for segment in viral_segments:
                start_h, start_m, start_s = map(int, segment["start_time"].split(":"))
                end_h, end_m, end_s = map(int, segment["end_time"].split(":"))
                
                start_seconds_total = start_h * 3600 + start_m * 60 + start_s
                end_seconds_total = end_h * 3600 + end_m * 60 + end_s
                
                segment_duration = end_seconds_total - start_seconds_total
                
                if segment_duration < 45:
                    # Extend the segment to meet the 45-second requirement.
                    end_seconds_total = start_seconds_total + 45
                elif segment_duration > 100:
                    # Trim the segment to meet the 100-second requirement.
                    end_seconds_total = start_seconds_total + 100
                
                # Convert total seconds back to HH:MM:SS format.
                end_h, remainder = divmod(end_seconds_total, 3600)
                end_m, end_s = divmod(remainder, 60)
                
                segment["end_time"] = f"{end_h:02}:{end_m:02}:{end_s:02}"


    
            print("Generating Shorts...")
            update_cache(video_id, viral_response)
            generated_files = create_shorts(video_path, viral_segments)
            print("Zipping videos...")
            zip_the_files(generated_files, f"{request_code}.zip")
    else:
        if video_id:
            print("Downloading video...")
            video_path = download_youtube_video(video_id)
        print("Generating Shorts...")
        print(cviral_response)
        try:
            viral_segments = json.loads(cviral_response)["segments"]
        except Exception as e:
            viral_segments = json.loads(cviral_response)
        generated_files = create_shorts(video_path, viral_segments)
        print("Zipping videos...")
        zip_the_files(generated_files, f"{request_code}.zip")

# ViralEm(key="", video_id="https://www.youtube.com/watch?v=T6h2kF-BIZc", request_code=uuid.uuid4())
