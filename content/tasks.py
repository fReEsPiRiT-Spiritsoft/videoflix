"""Background tasks for video processing and HLS conversion.

This module provides Django RQ tasks for converting uploaded videos into
HLS (HTTP Live Streaming) format with multiple resolution variants.
"""

import json
import os
import subprocess

from django.conf import settings

from content.models import Video, VideoResolution


def get_video_resolutions():
    """Get supported video resolution configurations.
    
    Returns:
        list: Tuples of (resolution_name, width, height, bitrate) for each quality level.
    """
    return [
        ('480p', 854, 480, '1000k'),
        ('720p', 1280, 720, '2500k'),
        ('1080p', 1920, 1080, '5000k'),
    ]


def get_video_duration(input_path):
    """Get video duration in seconds using ffprobe.
    
    Args:
        input_path: Path to video file.
        
    Returns:
        float: Duration in seconds, or None if error.
    """
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
           '-of', 'json', input_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            return float(data['format']['duration'])
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  x Error parsing duration: {e}")
            return None
    print(f"  x ffprobe error: {result.stderr}")
    return None


def get_thumbnail_path(video_id):
    """Build thumbnail file path with year/month directory structure.
    
    Args:
        video_id: ID of the video.
        
    Returns:
        str: Full path to thumbnail file.
    """
    from datetime import datetime
    now = datetime.now()
    thumb_dir = os.path.join(settings.MEDIA_ROOT, 'thumbnails', 
                             str(now.year), f'{now.month:02d}')
    os.makedirs(thumb_dir, exist_ok=True)
    return os.path.join(thumb_dir, f'{video_id}.jpg')


def generate_thumbnail(video_id, input_path):
    """Generate thumbnail from middle of video.
    
    Args:
        video_id: ID of the video.
        input_path: Path to input video file.
        
    Returns:
        str: Path to generated thumbnail, or None if error.
    """
    print(f"    -> Getting video duration...")
    duration = get_video_duration(input_path)
    if not duration:
        print(f"    x Failed to get video duration")
        return None
    
    timestamp = duration / 2
    print(f"    -> Extracting frame at {timestamp:.1f}s...")
    thumbnail_path = get_thumbnail_path(video_id)
    cmd = ['ffmpeg', '-ss', str(timestamp), '-i', input_path, '-vframes', '1',
           '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease',
           '-q:v', '2', thumbnail_path, '-y']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"    x FFmpeg error: {result.stderr[:200]}")
        return None
    
    print(f"    + Thumbnail created at {thumbnail_path}")
    return thumbnail_path


def save_thumbnail_to_video(video, thumbnail_path):
    """Save generated thumbnail to Video model.
    
    Args:
        video: Video instance to update.
        thumbnail_path: Path to thumbnail file.
    """
    if not thumbnail_path or not os.path.exists(thumbnail_path):
        print(f"    x Thumbnail file not found: {thumbnail_path}")
        return
    
    relative_path = os.path.relpath(thumbnail_path, settings.MEDIA_ROOT)
    video.thumbnail = relative_path
    video.save(update_fields=['thumbnail'])
    print(f"    + Thumbnail saved to DB: {relative_path}")


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


def build_ffmpeg_command(input_path, output_dir, width, height, bitrate):
    """Build FFmpeg command for HLS conversion.
    
    Args:
        input_path: Path to input video file.
        output_dir: Directory for output HLS files.
        width: Video width in pixels.
        height: Video height in pixels.
        bitrate: Video bitrate (e.g., '2500k').
        
    Returns:
        list: FFmpeg command arguments.
    """
    output_playlist = os.path.join(output_dir, 'index.m3u8')
    return [
        'ffmpeg', '-i', input_path,
        '-vf', f'scale={width}:{height}',
        '-c:v', 'libx264', '-b:v', bitrate,
        '-c:a', 'aac', '-b:a', '128k',
        '-hls_time', '10', '-hls_playlist_type', 'vod',
        '-hls_segment_filename', os.path.join(output_dir, 'segment%03d.ts'),
        output_playlist, '-y'
    ]


def convert_video_resolution(input_path, output_dir, res_name, width, height, bitrate):
    """Convert video to a specific resolution using FFmpeg.
    
    Args:
        input_path: Path to input video file.
        output_dir: Directory for output HLS files.
        res_name: Resolution name (e.g., '720p').
        width: Video width in pixels.
        height: Video height in pixels.
        bitrate: Video bitrate.
        
    Returns:
        bool: True if conversion succeeded, False otherwise.
    """
    os.makedirs(output_dir, exist_ok=True)
    cmd = build_ffmpeg_command(input_path, output_dir, width, height, bitrate)
    
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


def create_master_playlist(hls_base_dir):
    """Create HLS master playlist for adaptive bitrate streaming.
    
    Generates a master.m3u8 file that references all available resolutions,
    enabling automatic quality switching based on bandwidth.
    
    Args:
        hls_base_dir: Base directory for HLS files.
    """
    master_playlist_path = os.path.join(hls_base_dir, 'master.m3u8')
    
    with open(master_playlist_path, 'w') as f:
        f.write('#EXTM3U\n')
        f.write('#EXT-X-VERSION:3\n\n')
        
        for res_name, width, height, bitrate in get_video_resolutions():
            bandwidth = int(bitrate.replace('k', '000')) + 128000
            f.write(f'#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={width}x{height}\n')
            f.write(f'{res_name}/index.m3u8\n\n')
    
    print("  + Master playlist created for adaptive bitrate streaming!")


def process_all_resolutions(video, input_path, hls_base_dir):
    """Process all resolution variants for a video.
    
    Args:
        video: Video instance to process.
        input_path: Path to input video file.
        hls_base_dir: Base directory for HLS output.
    """
    for res_name, width, height, bitrate in get_video_resolutions():
        output_dir = os.path.join(hls_base_dir, res_name)
        success = convert_video_resolution(input_path, output_dir, res_name, width, height, bitrate)
        if success:
            save_video_resolution(video, res_name)
    
    create_master_playlist(hls_base_dir)


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
        print(f"Processing video: {video.title} ({video_id})")
        print(f"  Input path: {input_path}")
        
        # Generate thumbnail first for faster user feedback
        print("  -> Generating thumbnail...")
        try:
            video.refresh_from_db(fields=['thumbnail'])
            if not video.thumbnail:
                thumbnail_path = generate_thumbnail(video.id, input_path)
                if thumbnail_path:
                    save_thumbnail_to_video(video, thumbnail_path)
                else:
                    print("    x Thumbnail generation failed")
            else:
                print("    -> Custom thumbnail already set, skipping generation")
        except Exception as e:
            print(f"    x Thumbnail error: {str(e)}")
        
        # Process HLS resolutions
        hls_base_dir = create_hls_directory(video.id)
        process_all_resolutions(video, input_path, hls_base_dir)
        
        video.is_processed = True
        video.save(update_fields=['is_processed'])
        print(f" Video {video.title} processed successfully!")
        
    except Video.DoesNotExist:
        print(f"Video {video_id} not found")
    except Exception as e:
        print(f"Error processing video {video_id}: {str(e)}")