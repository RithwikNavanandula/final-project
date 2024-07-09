
from flask import redirect, session
from functools import wraps
import os
import subprocess
import cv2
import shutil
from werkzeug.utils import secure_filename




def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

UPLOAD_FOLDER = 'app.root_path/upload/'
COMPRESS_FOLDER = 'app.root_path/compress'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'flv', 'wmv'}

def save_video(username, video_file):
  """
  Saves a video file with the username incorporated into the path.

  Args:
      username (str): The username to include in the subfolder name.
      video_file (str): The path to the video file.

  Returns:
      str: The complete path where the video is saved.

  Raises:
      ValueError: If the username or video file path is empty.
      OSError: If there's an issue creating the folder structure.
  """

  if not username or not video_file:
    raise ValueError("Username and video file path cannot be empty.")

  # Extract video filename with extension
  video_filename = os.path.basename(video_file)

  # Create the specified folder structure
  specified_folder = "saved_videos"  # Customize this folder name
  user_subfolder = os.path.join(specified_folder, username)
  try:
    if not os.path.exists(specified_folder):
      os.makedirs(specified_folder)
    if not os.path.exists(user_subfolder):
      os.makedirs(user_subfolder)
  except OSError as e:
    raise OSError(f"Error creating folder structure: {e}")

  # Create the full path with username and filename
  final_path = os.path.join(user_subfolder, video_filename)

  # Handle potential file existence conflicts (optional)
  if os.path.exists(final_path):
    # Consider using a unique filename generation approach (e.g., timestamps)
    print(f"Warning: File '{video_filename}' already exists in '{user_subfolder}'.")
    # Implement your desired conflict resolution strategy here

  # Move (or copy) the video file to the final path
  shutil.move(video_file, final_path)  # Use shutil.copy2() if you want a copy

  return final_path

def compress_video(video_full_path, username, output_file_name):
    

    output_path = os.path.join(COMPRESS_FOLDER, username)
    os.makedirs(output_path, exist_ok=True)

    probe = subprocess.run(['ffmpeg', '-i', video_full_path], stderr=subprocess.PIPE, text=True)
    duration = float(probe.stderr.split('Duration: ')[1].split(',')[0])
    audio_bitrate = float(probe.stderr.split('Audio: ')[1].split()[0].replace('kb/s', ''))
    file_size = os.path.getsize(video_full_path)
    target_size = file_size * 0.1  # 10% of original size

    # Calculate target total bitrate
    target_total_bitrate = (target_size * 1024 * 8) / (1.073741824 * duration)

    # Calculate audio and video bitrates
    if 10 * audio_bitrate > target_total_bitrate:
        audio_bitrate = target_total_bitrate / 10
    elif audio_bitrate < 32000 < target_total_bitrate:
        audio_bitrate = 32000
    elif audio_bitrate > 256000:
        audio_bitrate = 256000

    video_bitrate = target_total_bitrate - audio_bitrate

    output_file_path = os.path.join(output_path, output_file_name)
    subprocess.run(['ffmpeg', '-i', video_full_path, '-c:v', 'libx264', '-b:v', str(video_bitrate),
                    '-pass', '1', '-f', 'mp4', os.devnull], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(['ffmpeg', '-i', video_full_path, '-c:v', 'libx264', '-b:v', str(video_bitrate),
                    '-pass', '2', '-c:a', 'aac', '-b:a', str(int(audio_bitrate)),
                    '-y', output_file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return output_file_path


