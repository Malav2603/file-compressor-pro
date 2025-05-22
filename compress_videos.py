import os
import subprocess
import argparse

def compress_video(input_file, output_file, bitrate='1000k'):
    command = [
        'ffmpeg',
        '-i', input_file,
        '-b:v', bitrate,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        output_file
    ]
    subprocess.run(command, check=True)

def process_directory(input_dir, output_dir, bitrate='1000k', video_extensions=('.mp4', '.mov')):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(video_extensions):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f'compressed_{filename}')
            print(f'Compressing {filename}...')
            compress_video(input_path, output_path, bitrate)
            print(f'Compressed {filename} saved to {output_path}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compress videos in batch using ffmpeg.')
    parser.add_argument('input_dir', help='Directory containing videos to compress')
    parser.add_argument('output_dir', help='Directory to save compressed videos')
    parser.add_argument('--bitrate', default='1000k', help='Bitrate for compression (default: 1000k)')
    args = parser.parse_args()
    
    process_directory(args.input_dir, args.output_dir, args.bitrate) 