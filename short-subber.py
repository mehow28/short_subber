import os
from pytube import YouTube
import math
import pysrt
from moviepy.editor import  TextClip, CompositeVideoClip, VideoFileClip, ImageClip
from youtube_transcript_api import YouTubeTranscriptApi

# to install necessary libs run this prompt: pip install -r requirements.txt

def download_video(url, filename):
    yt = YouTube(url)
    video = yt.streams.filter(file_extension='mp4').first()

    # Download the video
    video.download(filename=filename)

def get_transcript_as_srt(video_id):
    # Get the transcript for the given YouTube video ID
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    srt_content = ""
    subtitle_number = 1
    for entry in transcript:
        start_time = entry['start']
        duration = entry['duration']
        end_time = start_time + duration
        text = entry['text']

        start_time_seconds = str(start_time).split(".")[0]
        start_time_miliseconds = str(start_time).split(".")[1]
        start_time_minutes = math.floor(int(start_time_seconds)/60)
        start_time_seconds = int(start_time_seconds) - start_time_minutes*60

        end_time_seconds = str(end_time).split(".")[0]
        end_time_miliseconds = str(end_time).split(".")[1][0:3]
        end_time_minutes = math.floor(int(end_time_seconds)/60)
        end_time_seconds = int(end_time_seconds) - end_time_minutes*60

        # Format the start and end times in the SRT format (HH:MM:SS,mmm).
        start_time_formatted = "00:"+f"{start_time_minutes:02d}:"+f"{start_time_seconds:02d},"+f"{int(start_time_miliseconds):03d}"
        end_time_formatted = "00:"+f"{end_time_minutes:02d}:"+f"{end_time_seconds:02d},"+f"{int(end_time_miliseconds):03d}"

        # Create the subtitle entry in SRT format and append it to the SRT content.
        srt_entry = f"{subtitle_number}\n{start_time_formatted} --> {end_time_formatted}\n{text}\n\n"
        srt_content += srt_entry
        
        # Increment the subtitle number.
        subtitle_number += 1

    return srt_content

def time_to_seconds(time_obj):
    return time_obj.hours * 3600 + time_obj.minutes * 60 + time_obj.seconds + time_obj.milliseconds / 1000


def create_subtitle_clips(subtitles, videosize,fontsize=36, font='Arial', color='yellow', debug = False):
    subtitle_clips = []

    for subtitle in subtitles:
        start_time = time_to_seconds(subtitle.start)
        end_time = time_to_seconds(subtitle.end)
        duration = end_time - start_time

        video_width, video_height = videosize
        
        text_clip = TextClip(subtitle.text, fontsize=fontsize, font=font, color=color, bg_color = 'black',size=(video_width, None), method='caption').set_start(start_time).set_duration(duration)
        subtitle_x_position = 'center'
        subtitle_y_position = video_height* 4 / 5 

        text_position = (subtitle_x_position, subtitle_y_position)                    
        subtitle_clips.append(text_clip.set_position(text_position))

    return subtitle_clips

def add_subs_to_video(mp4filename,srtfilename):
    video = VideoFileClip(mp4filename)
    subtitles = pysrt.open(srtfilename)
    tempfileName = "temp.mp4"
    begin = mp4filename.split(".mp4")[0]
    output_video_file = begin + '_subtitled'+".mp4"

    print ("Output file name: ",output_video_file)
    resizedVid = video.resize(width=1080)
    black_image = ImageClip("black_picture_1920x1080.jpg",duration=59)
    backgrounded_vid = CompositeVideoClip([black_image, resizedVid.set_position("center")])
    backgrounded_vid.write_videofile(tempfileName)
    backgrounded_vid = VideoFileClip(tempfileName)
   
    # Create subtitle clips
    subtitle_clips = create_subtitle_clips(subtitles,backgrounded_vid.size)

    # Add subtitles to the video
    final_video = CompositeVideoClip([backgrounded_vid] + subtitle_clips)

    # Write output video file
    final_video.write_videofile(output_video_file)
    os.remove(tempfileName)

def main():
    video_id='' # Enter your desired video id
    url = 'https://www.youtube.com/watch?v='+video_id  # Replace with your video's URL
    vidname = video_id+'.mp4'
    subname = 'subs.srt'
    download_video(url,vidname)
    
    with open(subname, 'w', encoding='utf-8') as output_file:
        output_file.write(get_transcript_as_srt(video_id))
    
    add_subs_to_video(vidname,subname)
    os.remove(subname)
    os.remove(vidname)

main()