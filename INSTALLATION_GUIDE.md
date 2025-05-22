# Video Compressor Installation Guide

## For macOS Users

1. Download the `Video Compressor.app.zip` file
2. Extract the ZIP file
3. Double-click `Video Compressor.app` to run the application
4. If you see a security warning:
   - Go to System Preferences > Security & Privacy
   - Click "Open Anyway" for the Video Compressor app

## Prerequisites

The application requires FFmpeg to be installed on your system. If you don't have FFmpeg installed:

1. Open Terminal
2. Install Homebrew if you don't have it:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. Install FFmpeg:
   ```bash
   brew install ffmpeg
   ```

## Using the Application

1. Launch the Video Compressor app
2. Click "Select Videos" to choose the videos you want to compress
3. Click "Browse" to select where you want to save the compressed videos
4. Adjust the bitrate if needed (default is 1000k)
5. Click "Start Compression" to begin the process
6. Wait for the compression to complete
7. Find your compressed videos in the output directory you selected

## Troubleshooting

If you encounter any issues:

1. Make sure FFmpeg is installed correctly
2. Try running the application again
3. Check that you have enough disk space
4. Ensure you have permission to access the input and output directories

## Support

If you need help or encounter any issues, please contact the developer. 