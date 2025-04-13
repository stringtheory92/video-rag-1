#!/usr/bin/env python3
import duckdb
import json
import os
import argparse

def create_tables(con):
    # Create a table for videos.
    con.execute("""
    CREATE TABLE IF NOT EXISTS videos (
      video_id TEXT PRIMARY KEY,
      title TEXT,
      url TEXT,
      duration_sec INTEGER,
      topic TEXT
    );
    """)

    # Create table for segments.
    con.execute("""
    CREATE TABLE IF NOT EXISTS segments (
      segment_id TEXT PRIMARY KEY,
      video_id TEXT,
      start_time FLOAT,
      end_time FLOAT,
      text TEXT,
      caption TEXT,           -- Placeholder for multimodal data
      step_number INTEGER,    -- Optional, for procedural segments
      concept_tags TEXT[]     -- Placeholder for tags/keywords
    );
    """)

    # Create table for procedures.
    con.execute("""
    CREATE TABLE IF NOT EXISTS procedures (
      procedure_id TEXT PRIMARY KEY,
      video_id TEXT,
      name TEXT,
      description TEXT
    );
    """)

    # Create table for procedure steps.
    con.execute("""
    CREATE TABLE IF NOT EXISTS procedure_steps (
      step_id TEXT PRIMARY KEY,
      procedure_id TEXT,
      step_number INTEGER,
      title TEXT,
      description TEXT,
      start_time FLOAT,
      end_time FLOAT,
      text TEXT
    );
    """)

    # Create linking table for step segments (if a step maps to a particular segment).
    con.execute("""
    CREATE TABLE IF NOT EXISTS step_segments (
      procedure_id TEXT,
      step_id TEXT,
      segment_id TEXT
    );
    """)

def populate_tables(con, segmentation_data, video_metadata):
    """
    segmentation_data: dict with keys "segments" and "procedures" from analysis output.
    video_metadata: dict with metadata for the video (e.g. video_id, title, url, etc.)
    """
    video_id = video_metadata.get("video_id", "unknown_video")

    # Insert or update the video record.
    con.execute("""
    INSERT INTO videos (video_id, title, url, duration_sec, topic)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(video_id) DO NOTHING;
    """, (video_id, video_metadata.get("title", ""), video_metadata.get("url", ""),
          video_metadata.get("duration_sec", None), video_metadata.get("topic", "")))

    # Populate segments.
    segments = segmentation_data.get("segments", [])
    for seg in segments:
        con.execute("""
        INSERT INTO segments (segment_id, video_id, start_time, end_time, text)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(segment_id) DO NOTHING;
        """, (seg.get("segment_id"), video_id, seg.get("start_time"),
              seg.get("end_time"), seg.get("text")))

    # Populate procedures and procedure_steps if any.
    procedures = segmentation_data.get("procedures", [])
    for proc in procedures:
        proc_id = proc.get("procedure_id")
        con.execute("""
        INSERT INTO procedures (procedure_id, video_id, name, description)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(procedure_id) DO NOTHING;
        """, (proc_id, video_id, proc.get("name"), proc.get("description")))
        
        steps = proc.get("steps", [])
        for step in steps:
            con.execute("""
            INSERT INTO procedure_steps (step_id, procedure_id, step_number, title, description, start_time, end_time, text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(step_id) DO NOTHING;
            """, (step.get("step_id"), proc_id, step.get("step_number"), step.get("title"),
                  step.get("text"), step.get("start_time"), step.get("end_time"), step.get("text")))
            
            # Optionally, if you want to link a step to a particular segment, you could add that info.
            # For now, we'll assume each step corresponds to a segment with matching start_time/end_time.
            # This can be customized further as needed.
            # E.g.,
            # con.execute("INSERT INTO step_segments (procedure_id, step_id, segment_id) VALUES (?, ?, ?)",
            #             (proc_id, step.get("step_id"), corresponding_segment_id))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate DuckDB tables with video segmentation and procedure data.")
    parser.add_argument("segmentation_file", help="Path to the segmentation JSON file (from analysis script)")
    parser.add_argument("--db_path", default="videos.duckdb", help="DuckDB file path")
    parser.add_argument("--video_metadata", default="video_metadata.json", help="Path to a JSON file with video-level metadata")
    args = parser.parse_args()
    
    # Load segmentation data.
    with open(args.segmentation_file, "r", encoding="utf-8") as f:
        segmentation_data = json.load(f)
    
    # Load video metadata.
    # Example metadata keys: video_id, title, url, duration_sec, topic
    with open(args.video_metadata, "r", encoding="utf-8") as f:
        video_metadata = json.load(f)
    
    # Connect to DuckDB.
    con = duckdb.connect(args.db_path)
    create_tables(con)
    populate_tables(con, segmentation_data, video_metadata)
    
    print("DuckDB tables populated successfully.")
