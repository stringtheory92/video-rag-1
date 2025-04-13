#!/usr/bin/env python3
import os
import json
import argparse
import openai

def analyze_transcript(transcript_path: str, output_dir: str):
    # Read the transcript file.
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript_data = json.load(f)
    
    full_transcript = transcript_data.get("text", "")
    video_id = transcript_data.get("video_id", "unknown_video")
    
    # Define your prompt here.
    prompt = f"""
You are an expert assistant specialized in processing educational video content.
Given the following transcript of a beauty school video, identify:
1. Topic transitions: Split the transcript into segments, each representing a coherent topic.
2. Procedures: If any part of the transcript describes a process or procedure (with multiple steps), identify the procedure, its name, and break it into ordered steps.
   
Return a JSON object with two fields:
- "segments": an array of objects, each with:
  - "segment_id": a unique identifier (e.g. "seg1")
  - "video_id": the video_id from the transcript
  - "start_time": (in seconds) approximate start time of the segment (if not available, use null)
  - "end_time": (in seconds) approximate end time (or null)
  - "text": the text content of the segment
  
- "procedures": an array (can be empty) where each object has:
  - "procedure_id": a unique identifier (e.g. "proc1")
  - "name": a short descriptive name for the procedure (e.g. "Foil Application Process")
  - "description": a short description of the procedure
  - "steps": an array of objects, each with:
      - "step_id": a unique identifier (e.g. "step1")
      - "step_number": the order of the step (integer)
      - "title": a brief title for the step (e.g. "Apply developer")
      - "start_time": approximate start time in the transcript (or null)
      - "end_time": approximate end time (or null)
      - "text": the transcript text for that step

If no clear procedure is detected, return an empty array for "procedures".

Transcript:
\"\"\"{full_transcript}\"\"\"
"""
    print("Sending transcript to OpenAI for analysis...")
    # Call the API
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a video content analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    
    analysis_result = response.choices[0].message["content"]
    
    try:
        analysis_json = json.loads(analysis_result)
    except Exception as e:
        print("Error parsing JSON from OpenAI response:", e)
        print("Raw response:", analysis_result)
        raise e

    # Save the segmentation result.
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{video_id}_segmentation.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis_json, f, indent=2)
    
    print(f"Segmentation and procedure info saved to {output_file}")
    return analysis_json

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze transcript to segment topics and extract procedures.")
    parser.add_argument("transcript_path", help="Path to the transcript JSON file from Whisper extraction")
    parser.add_argument("--output_dir", default="analysis", help="Directory to save the segmentation JSON")
    args = parser.parse_args()

    analyze_transcript(args.transcript_path, args.output_dir)
