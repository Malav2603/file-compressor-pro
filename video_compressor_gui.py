import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import sys
import shutil
from threading import Thread
import queue
from PIL import Image, ImageTk
import fitz  # PyMuPDF for PDF handling
import customtkinter as ctk
from pathlib import Path

class ModernFileCompressor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("File Compressor Pro")
        self.geometry("800x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize variables
        self.input_files = []
        self.output_dir = ""
        self.current_tab = "compress"
        self.pdf_pages = []
        
        # Create main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create tabview
        self.tabview = ctk.CTkTabview(self.main_container)
        self.tabview.pack(fill="both", expand=True)
        
        # Create tabs
        self.tabview.add("Compress")
        self.tabview.add("PDF Tools")
        self.tabview.add("Settings")
        
        # Setup each tab
        self.setup_compress_tab()
        self.setup_pdf_tab()
        self.setup_settings_tab()
        
        # Message queue for thread communication
        self.queue = queue.Queue()
        self.after(100, self.check_queue)

    def setup_compress_tab(self):
        tab = self.tabview.tab("Compress")
        
        # File type selection
        file_type_frame = ctk.CTkFrame(tab)
        file_type_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(file_type_frame, text="File Type:").pack(side="left", padx=5)
        self.file_type = ctk.CTkOptionMenu(
            file_type_frame,
            values=["Videos", "Images", "PDFs", "All Files"],
            command=self.update_file_filters
        )
        self.file_type.pack(side="left", padx=5)
        
        # Input files section
        input_frame = ctk.CTkFrame(tab)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(input_frame, text="Input Files:").pack(side="left", padx=5)
        self.input_label = ctk.CTkLabel(input_frame, text="No files selected")
        self.input_label.pack(side="left", padx=5)
        ctk.CTkButton(
            input_frame,
            text="Select Files",
            command=self.select_input_files
        ).pack(side="right", padx=5)
        
        # Output directory section
        output_frame = ctk.CTkFrame(tab)
        output_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(output_frame, text="Output Directory:").pack(side="left", padx=5)
        self.output_label = ctk.CTkLabel(output_frame, text="No directory selected")
        self.output_label.pack(side="left", padx=5)
        ctk.CTkButton(
            output_frame,
            text="Browse",
            command=self.select_output_dir
        ).pack(side="right", padx=5)
        
        # Compression settings
        settings_frame = ctk.CTkFrame(tab)
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        # Quality slider and label
        quality_frame = ctk.CTkFrame(settings_frame)
        quality_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(quality_frame, text="Quality:").pack(side="left", padx=5)
        self.quality_slider = ctk.CTkSlider(
            quality_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.update_quality_label
        )
        self.quality_slider.pack(side="left", padx=5, fill="x", expand=True)
        self.quality_slider.set(80)
        
        # Quality percentage label
        self.quality_label = ctk.CTkLabel(quality_frame, text="80%")
        self.quality_label.pack(side="left", padx=5)
        
        # Progress section
        progress_frame = ctk.CTkFrame(tab)
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=5, pady=5)
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(progress_frame, text="Ready")
        self.status_label.pack(pady=5)
        
        # Start button
        self.start_button = ctk.CTkButton(
            tab,
            text="Start Compression",
            command=self.start_compression
        )
        self.start_button.pack(pady=10)

    def setup_pdf_tab(self):
        tab = self.tabview.tab("PDF Tools")
        
        # PDF operations
        operations_frame = ctk.CTkFrame(tab)
        operations_frame.pack(fill="x", padx=10, pady=5)
        
        # Merge PDFs section
        ctk.CTkLabel(operations_frame, text="Merge PDFs", font=("Helvetica", 16, "bold")).pack(pady=5)
        self.merge_files = []
        self.merge_list = ctk.CTkTextbox(operations_frame, height=200)
        self.merge_list.pack(fill="x", padx=5, pady=5)
        
        merge_buttons = ctk.CTkFrame(operations_frame)
        merge_buttons.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(
            merge_buttons,
            text="Add PDFs",
            command=self.add_pdfs_to_merge
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            merge_buttons,
            text="Clear List",
            command=lambda: self.merge_list.delete("1.0", "end")
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            merge_buttons,
            text="Merge PDFs",
            command=self.merge_pdfs
        ).pack(side="right", padx=5)

    def setup_settings_tab(self):
        tab = self.tabview.tab("Settings")
        
        # Theme selection
        theme_frame = ctk.CTkFrame(tab)
        theme_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(theme_frame, text="Theme:").pack(side="left", padx=5)
        self.theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Dark", "Light", "System"],
            command=self.change_theme
        )
        self.theme_menu.pack(side="left", padx=5)
        
        # Default settings
        settings_frame = ctk.CTkFrame(tab)
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        self.auto_open = ctk.CTkCheckBox(
            settings_frame,
            text="Auto-open output folder after compression"
        )
        self.auto_open.pack(pady=5)
        
        self.keep_original = ctk.CTkCheckBox(
            settings_frame,
            text="Keep original files"
        )
        self.keep_original.pack(pady=5)

    def update_file_filters(self, file_type):
        self.file_type.set(file_type)
        self.input_files = []
        self.input_label.configure(text="No files selected")

    def select_input_files(self):
        file_type = self.file_type.get()
        filetypes = {
            "Videos": [("Video files", "*.mp4 *.mov *.avi *.mkv")],
            "Images": [("Image files", "*.jpg *.jpeg *.png *.gif *.bmp")],
            "PDFs": [("PDF files", "*.pdf")],
            "All Files": [("All files", "*.*")]
        }
        
        files = filedialog.askopenfilenames(
            title="Select Files",
            filetypes=filetypes.get(file_type, [("All files", "*.*")])
        )
        
        if files:
            self.input_files = files
            self.input_label.configure(text=f"{len(files)} files selected")

    def select_output_dir(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir = directory
            self.output_label.configure(text=directory)

    def compress_file(self, input_file, output_file, quality):
        try:
            file_ext = os.path.splitext(input_file)[1].lower()
            
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                self.compress_image(input_file, output_file, quality)
            elif file_ext in ['.mp4', '.mov', '.avi', '.mkv']:
                self.compress_video(input_file, output_file, quality)
            elif file_ext == '.pdf':
                self.compress_pdf(input_file, output_file, quality)
            else:
                self.queue.put(('error', f"Unsupported file type: {file_ext}"))
                
        except Exception as e:
            self.queue.put(('error', f"Error compressing {os.path.basename(input_file)}: {str(e)}"))

    def compress_image(self, input_file, output_file, quality):
        with Image.open(input_file) as img:
            img.save(output_file, quality=quality, optimize=True)

    def compress_video(self, input_file, output_file, quality):
        # Convert quality (0-100) to bitrate
        bitrate = f"{int(quality * 20)}k"
        
        command = [
            'ffmpeg',
            '-i', input_file,
            '-c:v', 'libx264',
            '-b:v', bitrate,
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y',
            output_file
        ]
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        while True:
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                self.queue.put(('status', output.strip()))

    def compress_pdf(self, input_file, output_file, quality):
        # Convert quality (0-100) to PDF compression level
        compression_level = int(quality / 20)  # 0-5
        
        doc = fitz.open(input_file)
        for page in doc:
            page.clean_contents()
        doc.save(
            output_file,
            garbage=4,
            deflate=True,
            clean=True,
            linear=True
        )
        doc.close()

    def add_pdfs_to_merge(self):
        files = filedialog.askopenfilenames(
            title="Select PDFs to Merge",
            filetypes=[("PDF files", "*.pdf")]
        )
        
        if files:
            self.merge_files.extend(files)
            self.update_merge_list()

    def update_merge_list(self):
        self.merge_list.delete("1.0", "end")
        for i, file in enumerate(self.merge_files, 1):
            self.merge_list.insert("end", f"{i}. {os.path.basename(file)}\n")

    def merge_pdfs(self):
        if not self.merge_files:
            messagebox.showerror("Error", "Please add PDFs to merge")
            return
            
        output_file = filedialog.asksaveasfilename(
            title="Save Merged PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        
        if not output_file:
            return
            
        try:
            merger = fitz.open()
            for pdf in self.merge_files:
                merger.insert_pdf(fitz.open(pdf))
            merger.save(output_file)
            merger.close()
            messagebox.showinfo("Success", "PDFs merged successfully!")
            self.merge_files = []
            self.update_merge_list()
        except Exception as e:
            messagebox.showerror("Error", f"Error merging PDFs: {str(e)}")

    def change_theme(self, theme):
        ctk.set_appearance_mode(theme.lower())

    def start_compression(self):
        if not self.input_files:
            messagebox.showerror("Error", "Please select input files")
            return
        if not self.output_dir:
            messagebox.showerror("Error", "Please select output directory")
            return
        
        quality = int(self.quality_slider.get())
        self.start_button.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(text="Starting compression...")
        
        def compression_thread():
            total_files = len(self.input_files)
            for i, input_file in enumerate(self.input_files):
                filename = os.path.basename(input_file)
                output_file = os.path.join(self.output_dir, f"compressed_{filename}")
                
                self.queue.put(('progress', (i + 1) / total_files * 100))
                self.queue.put(('status', f"Compressing: {filename}"))
                
                self.compress_file(input_file, output_file, quality)
            
            self.queue.put(('complete', None))
        
        Thread(target=compression_thread, daemon=True).start()

    def check_queue(self):
        try:
            while True:
                msg_type, msg = self.queue.get_nowait()
                if msg_type == 'status':
                    self.status_label.configure(text=msg)
                elif msg_type == 'progress':
                    self.progress_bar.set(msg)
                elif msg_type == 'error':
                    messagebox.showerror("Error", msg)
                elif msg_type == 'complete':
                    self.start_button.configure(state="normal")
                    self.status_label.configure(text="Compression complete!")
                    messagebox.showinfo("Complete", "All files have been compressed successfully!")
                    if self.auto_open.get():
                        os.system(f"open {self.output_dir}")
                self.queue.task_done()
        except queue.Empty:
            pass
        self.after(100, self.check_queue)

    def update_quality_label(self, value):
        self.quality_label.configure(text=f"{int(value)}%")

def main():
    app = ModernFileCompressor()
    app.mainloop()

if __name__ == "__main__":
    main() 