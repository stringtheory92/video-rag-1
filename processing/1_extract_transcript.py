#!/usr/bin/env python3
import os
import json
# import whisper
# import argparse
import subprocess
import tempfile
from loguru import logger
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()






def extract_audio_from_video(video_path: str, output_dir: str = None):
    logger.info(f"Creating audio file from {video_path}")
    
    # Get base name without extension
    base_filename = os.path.splitext(os.path.basename(video_path))[0]
    audio_filename = f"{base_filename}_audio.wav"
    
    # Determine output directory
    output_dir = output_dir or os.path.dirname(video_path)
    audio_path = os.path.join(output_dir, audio_filename)

    try:
        logger.info("Beginning audio extraction")
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", 
            "-ar", "16000", "-ac", "1", audio_path
        ], check=True)
        logger.info(f"Extraction complete: {audio_path}")
    except Exception as e:
        print(f"Error extracting audio from video: {e}")
        return None
    
    return audio_path




def extract_transcript(audio_path: str, video_path: str, output_dir: str):
    client = OpenAI()
    
    try:
        audio_file = open(audio_path, "rb")

        transcription = client.audio.transcriptions.create(
        model="gpt-4o-mini-transcribe", 
        file=audio_file
        )
        # Ensure output directory exists.
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the transcript JSON. We include full transcript plus segments with start and end times.
        video_basename = os.path.basename(video_path)
        video_id = os.path.splitext(video_basename)[0]
        transcript_file = os.path.join(output_dir, f"{video_id}_transcript.json")
        
        with open(transcript_file, "w", encoding="utf-8") as f:
            json.dump({
                "video_id": video_id,
                "language": transcription.get("language", ""),
                "text": transcription.get("text", ""),
                "segments": transcription.get("segments", [])
            }, f, indent=2)
        
        print(f"Transcript saved to {transcript_file}")

    finally:
        # Clean up the temporary audio file
        if os.path.exists(audio_path):
            os.unlink(audio_path)

def main(video_path: str=os.environ.get("RAW_VIDEOS_PATH"), output_dir: str=os.environ.get("TRANSCRIPT_PATH")):
    audio_path = extract_audio_from_video(video_path)
    extract_transcript(audio_path, video_path, output_dir)

if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Extract transcript from a video using Whisper.")
    # parser.add_argument("video_path", help="Path to the video file (e.g., video.mp4)", required=False)
    # parser.add_argument("--output_dir", default="transcripts", help="Directory to save the transcript JSON", required=False)
    # args = parser.parse_args()
    
    # extract_transcript(args.video_path, args.output_dir)
    logger.info(os.environ.get("RAW_VIDEOS_PATH"))
    extract_audio_from_video(os.environ.get("RAW_VIDEOS_PATH"))
