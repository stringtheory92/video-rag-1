#!/usr/bin/env python3
import os
import json
import whisper
import argparse
import subprocess
import tempfile
from loguru import logger
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()






def extract_audio_from_video(video_path: str):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        temp_audio_path = temp_audio.name
    
    try:

        subprocess.run([
            "ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le", 
            "-ar", "16000", "-ac", "1", temp_audio_path
        ], check=True, capture_output=True)
    except Exception as e:
        print(f"Error extracting audio from video: {e}")
        return None
    return temp_audio_path





def extract_transcript(audio_path: str, video_path: str, output_dir: str):
    client = OpenAI()
    
    try:
        # # Load the Whisper model (using the small model for speed; adjust as needed)
        # print("Loading Whisper model...")
        # model = whisper.load_model("small")
        # # Transcribe the video.
        # print(f"Transcribing video: {video_path}")
        # result = model.transcribe(video_path)

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
