import cv2
import yaml
from datetime import datetime, timedelta
import threading
import time
import os
import json
import uuid
from PIL import Image

def record_rtsp_stream(name, url, group, output_file_prefix, segment_duration_min, max_video_age_days, output_directory, metadata_directory, frame_width, frame_height, file_format, save_screenshot=False, retry_count=3, retry_delay=5):
    try_count = 0
    while try_count < retry_count:
        try:
            # Buka koneksi ke stream RTSP
            cap = cv2.VideoCapture(url)

            if not cap.isOpened():
                print(f"Error: Tidak dapat membuka stream {url}")
                try_count += 1
                time.sleep(retry_delay)
                continue

            # Mendapatkan FPS (Frame per Second) dari video
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            if fps == 0:  # Jika tidak dapat mendapatkan FPS, gunakan default
                fps = 30
            print(f"FPS: {fps}")

            # Mengatur ukuran frame jika ditentukan, atau gunakan ukuran frame default
            original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            width = frame_width if frame_width is not None else original_width
            height = frame_height if frame_height is not None else original_height
            print(f"Resolution: {width} x {height}")

            # Menentukan codec dan ekstensi file berdasarkan format yang diinginkan
            if file_format.lower() == 'avi':
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                file_extension = '.avi'
            else:  # Default ke MP4
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                file_extension = '.mp4'

            while True:
                current_time = datetime.now()
                date_str = current_time.strftime('%Y%m%d')
                group_directory = os.path.join(output_directory, date_str)

                # Buat folder berdasarkan tanggal jika belum ada
                if not os.path.exists(group_directory):
                    os.makedirs(group_directory)

                end_time = current_time + timedelta(minutes=segment_duration_min)
                
                # Generate output file name with timestamp
                output_file = f"{output_file_prefix}_{current_time.strftime('%Y%m%d_%H%M%S')}{file_extension}"
                output_path = os.path.join(group_directory, output_file)
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

                frame_count = 0
                first_frame_saved = False
                screenshot_path = ""

                while datetime.now() < end_time:
                    ret, frame = cap.read()
                    if not ret:
                        print(f"Error: Tidak dapat membaca frame dari {url}")
                        break

                    # Resize frame if necessary
                    if frame_width is not None and frame_height is not None:
                        frame = cv2.resize(frame, (width, height))

                    out.write(frame)
                    frame_count += 1

                    # Save the first frame as a compressed screenshot
                    if save_screenshot and not first_frame_saved:
                        screenshot_file = f"{output_file_prefix}_{current_time.strftime('%Y%m%d_%H%M%S')}.png"
                        screenshot_path = os.path.join(group_directory, screenshot_file)
                        cv2.imwrite(screenshot_path, frame)
                        
                        # Compress screenshot
                        with Image.open(screenshot_path) as img:
                            img.save(screenshot_path, format="PNG", optimize=True, quality=85)

                        first_frame_saved = True

                # Calculate duration
                duration = frame_count / fps

                # Release the video writer
                out.release()
                print(f"Rekaman selesai: {output_path}")

                # Get file size
                file_size = os.path.getsize(output_path)

                # Save metadata to JSON file
                metadata_entry = {
                    "id": str(uuid.uuid4()),  # Generate unique ID
                    "name": name,
                    "group": group,
                    "recorded_at": current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "duration": duration,
                    "full_path": output_path,
                    "screenshot_path": screenshot_path if save_screenshot else "",
                    "fps": fps,
                    "resolution": f"{width}x{height}",
                    "file_size": file_size,
                    "month": current_time.month,
                    "day": current_time.weekday(),  # Monday is 0 and Sunday is 6
                    "date": current_time.day,
                    "time": current_time.strftime('%H:%M:%S')
                }

                # Path to metadata.json
                metadata_file = os.path.join(metadata_directory, 'metadata.json')

                # Append metadata entry to the JSON metadata file
                if os.path.exists(metadata_file):
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                else:
                    metadata = []

                metadata.append(metadata_entry)

                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=4)
                print(f"Metadata updated: {metadata_file}")

                if not ret:
                    try_count += 1
                    time.sleep(retry_delay)
                    break
                else:
                    try_count = 0  # Reset the retry counter if successful

                # Delete old videos
                delete_old_videos(output_file_prefix, max_video_age_days, output_directory, metadata_file)

            if try_count >= retry_count:
                print(f"Gagal merekam dari {url} setelah {retry_count} kali percobaan.")
                break

        except Exception as e:
            print(f"Exception occurred while recording from {url}: {e}")
            try_count += 1
            time.sleep(retry_delay)

        finally:
            # Menutup video capture
            if 'cap' in locals():
                cap.release()

def delete_old_videos(output_file_prefix, max_video_age_days, output_directory, metadata_file):
    current_time = datetime.now()
    cutoff_time = current_time - timedelta(days=max_video_age_days)

    for root, dirs, files in os.walk(output_directory):
        for filename in files:
            if filename.startswith(output_file_prefix) and (filename.endswith('.mp4') or filename.endswith('.avi') or filename.endswith('.png')):
                file_time_str = filename[len(output_file_prefix) + 1:-4]
                file_time = datetime.strptime(file_time_str, '%Y%m%d_%H%M%S')
                if file_time < cutoff_time:
                    file_path = os.path.join(root, filename)
                    os.remove(file_path)
                    print(f"Deleted old file: {file_path}")

                    # Remove corresponding metadata entry
                    if os.path.exists(metadata_file):
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)

                        metadata = [entry for entry in metadata if entry['full_path'] != file_path and entry.get('screenshot_path') != file_path]

                        with open(metadata_file, 'w') as f:
                            json.dump(metadata, f, indent=4)
                        print(f"Deleted metadata entry for: {file_path}")

def record_multiple_webcams(config_file):
    try:
        # Baca konfigurasi dari file YAML
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        if 'webcams' in config:
            threads = []
            for webcam in config['webcams']:
                name = webcam.get('name', 'Webcam')
                url = webcam.get('url', '')
                group = webcam.get('group', 'Uncategorized')
                segment_duration_min = webcam.get('segment_duration_min', 15)
                max_video_age_days = webcam.get('max_video_age_days', 10)
                output_directory = webcam.get('output_directory', '.')
                metadata_directory = webcam.get('metadata_directory', '.')  # New configuration option for metadata directory
                frame_width = webcam.get('frame_width', None)
                frame_height = webcam.get('frame_height', None)
                file_format = webcam.get('file_format', 'mp4')  # Default to 'mp4'
                save_screenshot = webcam.get('save_screenshot', False)  # Default to False
                retry_count = webcam.get('retry_count', 3)
                retry_delay = webcam.get('retry_delay', 5)

                # Ensure output and metadata directories exist
                if not os.path.exists(output_directory):
                    os.makedirs(output_directory)
                if not os.path.exists(metadata_directory):
                    os.makedirs(metadata_directory)

                # Create a new thread for each webcam
                thread = threading.Thread(target=record_rtsp_stream, args=(
                    name, url, group, name.replace(' ', '_'), segment_duration_min, max_video_age_days, output_directory, metadata_directory, frame_width, frame_height, file_format, save_screenshot, retry_count, retry_delay))
                thread.start()
                threads.append(thread)

            # Join all threads
            for thread in threads:
                thread.join()

    except Exception as e:
        print(f"Exception occurred while reading config file: {e}")

if __name__ == "__main__":
    config_file = "webcam_config.yaml"
    record_multiple_webcams(config_file)
