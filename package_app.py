import os
import shutil
import subprocess
import sys

def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def copy_ffmpeg():
    # Get FFmpeg path
    try:
        ffmpeg_path = subprocess.check_output(['which', 'ffmpeg']).decode().strip()
    except subprocess.CalledProcessError:
        print("Error: Could not find FFmpeg installation")
        return False
    
    # Create dist directory if it doesn't exist
    os.makedirs('dist', exist_ok=True)
    
    # Copy FFmpeg to dist directory
    shutil.copy2(ffmpeg_path, 'dist/ffmpeg')
    print(f"Copied FFmpeg from {ffmpeg_path} to dist/ffmpeg")
    return True

def main():
    print("Checking for FFmpeg...")
    if not check_ffmpeg():
        print("Error: FFmpeg is not installed. Please install FFmpeg first.")
        print("You can install it using: brew install ffmpeg")
        sys.exit(1)
    
    print("Copying FFmpeg to dist directory...")
    if not copy_ffmpeg():
        sys.exit(1)
    
    print("Building application...")
    os.system('pyinstaller --onefile --windowed --name "Video Compressor" --add-data "dist/ffmpeg:." video_compressor_gui.py')
    
    print("Creating distribution package...")
    # Create a distribution directory
    dist_dir = "Video_Compressor_Setup"
    os.makedirs(dist_dir, exist_ok=True)
    
    # Copy the application
    shutil.copytree(
        "dist/Video Compressor.app",
        os.path.join(dist_dir, "Video Compressor.app"),
        dirs_exist_ok=True
    )
    
    # Copy the installer
    shutil.copy2("install.py", dist_dir)
    shutil.copy2("install.command", dist_dir)
    
    # Create a README
    with open(os.path.join(dist_dir, "README.txt"), "w") as f:
        f.write("""Video Compressor Setup

To install Video Compressor:

1. Double-click 'install.command'
2. Follow the installation wizard
3. The application will be installed in your Applications folder
4. A shortcut will be created on your desktop

If you have any issues, please contact support.
""")
    
    # Create the final ZIP file
    print("Creating ZIP file...")
    os.system(f'zip -r "Video_Compressor_Setup.zip" "{dist_dir}"')
    
    print("\nDone! The setup package is in Video_Compressor_Setup.zip")
    print("Share this ZIP file with users. They just need to:")
    print("1. Extract the ZIP file")
    print("2. Double-click install.command")
    print("3. Follow the installation wizard")

if __name__ == "__main__":
    main() 