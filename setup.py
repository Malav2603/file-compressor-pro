from setuptools import setup

setup(
    name="video_compressor_gui",
    version="1.0",
    description="A GUI application for compressing videos using FFmpeg",
    author="Your Name",
    packages=["video_compressor_gui"],
    install_requires=[
        "tkinter",
    ],
    entry_points={
        'console_scripts': [
            'video_compressor=video_compressor_gui:main',
        ],
    },
) 