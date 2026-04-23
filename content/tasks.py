import os
import subprocess
from pathlib import Path
from django.conf import settings
from content.models import Video, VideoResolution

def process_video(video_id):
    """
    Konvertiert ein Video zu HLS in 480p, 720p, 1080p
    """
    try:
        video = Video.objects.get(id=video_id)
        
        if not video.video_file:
            print(f"Video {video_id} hat keine Datei")
            return
        
        # Pfade - NEU: Mit video.id für HLS-Struktur
        input_path = video.video_file.path
        hls_base_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(video.id))
        os.makedirs(hls_base_dir, exist_ok=True)
        
        print(f"Verarbeite Video: {video.title} ({video_id})")
        
        # HLS Ordner erstellen
        resolutions = [
            ('480p', '854:480', '1000k'),
            ('720p', '1280:720', '2500k'),
            ('1080p', '1920:1080', '5000k'),
        ]
        
        for res_name, scale, bitrate in resolutions:
            output_dir = os.path.join(hls_base_dir, res_name)
            os.makedirs(output_dir, exist_ok=True)
            
            output_playlist = os.path.join(output_dir, 'index.m3u8')
            
            # FFmpeg Befehl
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', f'scale={scale}',
                '-c:v', 'libx264',
                '-b:v', bitrate,
                '-c:a', 'aac',
                '-b:a', '128k',
                '-hls_time', '10',
                '-hls_playlist_type', 'vod',
                '-hls_segment_filename', os.path.join(output_dir, 'segment%03d.ts'),
                output_playlist,
                '-y'
            ]
            
            print(f"  → Erstelle {res_name}...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"  ✗ Fehler bei {res_name}: {result.stderr}")
                continue
            
            print(f"  ✓ {res_name} erstellt!")
            
            # VideoResolution in DB speichern
            VideoResolution.objects.update_or_create(
                video=video,
                resolution=res_name,
                defaults={
                    'hls_playlist': f"videos/hls/{video.id}/{res_name}/index.m3u8",
                    'is_ready': True
                }
            )
        
        # Video als verarbeitet markieren
        video.is_processed = True
        video.save()
        
        print(f" Video {video.title} erfolgreich verarbeitet!")
        
    except Video.DoesNotExist:
        print(f"Video {video_id} nicht gefunden")
    except Exception as e:
        print(f"Fehler beim Verarbeiten von Video {video_id}: {str(e)}")