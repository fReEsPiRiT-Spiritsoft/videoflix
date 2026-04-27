"""Background tasks for video processing and HLS conversion.

This module provides Django RQ tasks for converting uploaded videos into
HLS (HTTP Live Streaming) format with multiple resolution variants.
"""

import os
import subprocess
from pathlib import Path
from django.conf import settings
from content.models import Video, VideoResolution


def get_video_resolutions():
    """Get supported video resolution configurations.
    
    Returns:
        list: Tuples of (resolution_name, scale, bitrate) for each quality level.
    """
    return [
        ('480p', '854:480', '1000k'),
        ('720p', '1280:720', '2500k'),
        ('1080p', '1920:1080', '5000k'),
    ]


def create_hls_directory(video_id):
    """Create HLS base directory for a video.
    
    Args:
        video_id: ID of the video to create directory for.
        
    Returns:
        str: Path to created HLS directory.
    """
    hls_base_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(video_id))
    os.makedirs(hls_base_dir, exist_ok=True)
    return hls_base_dir


def build_ffmpeg_command(input_path, output_dir, scale, bitrate):
    """Build FFmpeg command for HLS conversion.
    
    Args:
        input_path: Path to input video file.
        output_dir: Directory for output HLS files.
        scale: Video scale parameter (e.g., '1280:720').
        bitrate: Video bitrate (e.g., '2500k').
        
    Returns:
        list: FFmpeg command arguments.
    """
    output_playlist = os.path.join(output_dir, 'index.m3u8')
    return [
        'ffmpeg', '-i', input_path,
        '-vf', f'scale={scale}',
        '-c:v', 'libx264', '-b:v', bitrate,
        '-c:a', 'aac', '-b:a', '128k',
        '-hls_time', '10', '-hls_playlist_type', 'vod',
        '-hls_segment_filename', os.path.join(output_dir, 'segment%03d.ts'),
        output_playlist, '-y'
    ]


def convert_video_resolution(input_path, output_dir, res_name, scale, bitrate):
    """Convert video to a specific resolution using FFmpeg.
    
    Args:
        input_path: Path to input video file.
        output_dir: Directory for output HLS files.
        res_name: Resolution name (e.g., '720p').
        scale: Video scale parameter.
        bitrate: Video bitrate.
        
    Returns:
        bool: True if conversion succeeded, False otherwise.
    """
    os.makedirs(output_dir, exist_ok=True)
    cmd = build_ffmpeg_command(input_path, output_dir, scale, bitrate)
    
    print(f"  -> Creating {res_name}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"  x Error with {res_name}: {result.stderr}")
        return False
    
    print(f"  + {res_name} created!")
    return True


def save_video_resolution(video, res_name):
    """Save VideoResolution entry to database.
    
    Args:
        video: Video instance to save resolution for.
        res_name: Resolution name (e.g., '720p').
    """
    VideoResolution.objects.update_or_create(
        video=video,
        resolution=res_name,
        defaults={
            'hls_playlist': f"videos/hls/{video.id}/{res_name}/index.m3u8",
            'is_ready': True
        }
    )


def process_all_resolutions(video, input_path, hls_base_dir):
    """Process all resolution variants for a video.
    
    Args:
        video: Video instance to process.
        input_path: Path to input video file.
        hls_base_dir: Base directory for HLS output.
    """
    for res_name, scale, bitrate in get_video_resolutions():
        output_dir = os.path.join(hls_base_dir, res_name)
        success = convert_video_resolution(input_path, output_dir, res_name, scale, bitrate)
        if success:
            save_video_resolution(video, res_name)


def process_video(video_id):
    """Convert a video to HLS format with 480p, 720p, and 1080p resolutions.
    
    Main entry point for video processing background task. Converts the
    uploaded video into HLS format with multiple quality levels.
    
    Args:
        video_id: ID of the video to process.
    """
    try:
        video = Video.objects.get(id=video_id)
        if not video.video_file:
            print(f"Video {video_id} has no file")
            return
        
        input_path = video.video_file.path
        hls_base_dir = create_hls_directory(video.id)
        print(f"Processing video: {video.title} ({video_id})")
        
        process_all_resolutions(video, input_path, hls_base_dir)
        
        video.is_processed = True
        video.save()
        print(f" Video {video.title} processed successfully!")
        
    except Video.DoesNotExist:
        print(f"Video {video_id} not found")
    except Exception as e:
        print(f"Error processing video {video_id}: {str(e)}")