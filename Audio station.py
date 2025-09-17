import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import tempfile
import sqlite3
import pygame.mixer
import threading
import requests
from pydub import AudioSegment
import subprocess
import platform

# --- IMPORTANT PREREQUISITES ---
# 1. You must install the required libraries:
#    pip install pydub
#    pip install pygame
#    pip install requests
# 2. You need FFmpeg, a command-line tool for handling multimedia files.
#    This program will now attempt to check for and install it.

class MusicDatabase:
    """Handles all database operations for music tracks."""
    def __init__(self, db_name="music_library.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """Creates the songs table if it doesn't exist."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY,
                path TEXT UNIQUE,
                title TEXT NOT NULL,
                play_count INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    def add_song(self, path, title):
        """Adds a new song to the database if it doesn't exist."""
        try:
            self.cursor.execute("INSERT INTO songs (path, title) VALUES (?, ?)", (path, title))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Song with this path already exists
            return False

    def get_all_songs(self):
        """Retrieves all songs from the database."""
        self.cursor.execute("SELECT path, title, play_count FROM songs")
        return self.cursor.fetchall()
        
    def search_songs(self, query):
        """Searches for songs in the database by title."""
        self.cursor.execute("SELECT path, title, play_count FROM songs WHERE title LIKE ?", ('%' + query + '%',))
        return self.cursor.fetchall()

    def increment_play_count(self, path):
        """Increments the play count for a song."""
        self.cursor.execute("UPDATE songs SET play_count = play_count + 1 WHERE path = ?", (path,))
        self.conn.commit()

    def get_recommendations(self):
        """Returns a list of songs ordered by their play count (most listened)."""
        self.cursor.execute("SELECT path, title, play_count FROM songs ORDER BY play_count DESC")
        return self.cursor.fetchall()

    def remove_song(self, path):
        """Removes a song from the database by its file path."""
        self.cursor.execute("DELETE FROM songs WHERE path = ?", (path,))
        self.conn.commit()

    def close(self):
        """Closes the database connection."""
        self.conn.close()

class AudioStationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Station")
        self.geometry("800x600")
        self.configure(bg="#2c3e50")

        self.audio_file_path = None
        self.audio_segment = None
        self.is_paused = False
        self.is_playing = False
        self.is_radio = False
        self.loop_music_var = tk.BooleanVar(value=False)
        self.db = MusicDatabase()

        # Check for FFmpeg on startup
        self.check_and_install_ffmpeg()

        # Initialize the pygame mixer
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.music.set_volume(0.5)
        
        # Dictionary of radio stations and their stream URLs and descriptions
        self.radio_stations = {
            "KQED (NPR)": {
                "url": "https://streams.kqed.org",
                "description": "Your public media source for news and cultural content. Stay informed with national and local news."
            },
            "BBC Radio 1": {
                "url": "http://stream.live.vc.bbcmedia.co.uk/bbc_radio_one",
                "description": "Playing the freshest new music and the biggest tracks from the hottest artists."
            },
            "NPR News": {
                "url": "https://npr-ice.streamguys1.com/nprlive-mp3",
                "description": "Listen to breaking news and top stories from NPR on demand."
            }
        }

        # Style configuration for a modern look
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#2c3e50")
        self.style.configure("TLabel", background="#2c3e50", foreground="#ecf0f1", font=("Helvetica", 12))
        self.style.configure("TButton", background="#34495e", foreground="#ecf0f1", borderwidth=0, font=("Helvetica", 12))
        self.style.map("TButton", background=[('active', '#5d6d7e')])
        self.style.configure("TCheckbutton", background="#2c3e50", foreground="#ecf0f1", font=("Helvetica", 10))
        self.style.configure("Horizontal.TScale", background="#2c3e50", troughcolor="#34495e", sliderrelief="flat")
        self.style.configure("Radio.TButton", font=("Helvetica", 14, "bold"), padding=10)
        self.style.configure("Description.TLabel", font=("Helvetica", 10, "italic"), foreground="#bdc3c7")

        self.main_frame = ttk.Frame(self, padding="20")
        self.main_frame.pack(fill="both", expand=True)

        self.radio_frame = ttk.Frame(self, padding="20")
        
        self.create_widgets()
        self.update_recommendations_listbox()
        self.after_id = None

    def check_and_install_ffmpeg(self):
        """Checks for FFmpeg and installs it if not found."""
        try:
            subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
            messagebox.showinfo("FFmpeg Status", "FFmpeg is already installed.")
        except FileNotFoundError:
            messagebox.showwarning("FFmpeg Status", "FFmpeg not found. Attempting to install...")
            os_name = platform.system()
            try:
                if os_name == "Windows":
                    messagebox.showinfo("FFmpeg Installation", "Please download and install FFmpeg manually from https://ffmpeg.org/download.html\nThen add the '/bin' folder to your system's PATH.")
                elif os_name == "Darwin": # macOS
                    try:
                        # Check for Homebrew
                        subprocess.run(["brew", "--version"], check=True, capture_output=True)
                        messagebox.showinfo("FFmpeg Installation", "Installing FFmpeg with Homebrew...")
                        subprocess.run(["brew", "install", "ffmpeg"], check=True)
                        messagebox.showinfo("FFmpeg Installation", "FFmpeg installed successfully.")
                    except FileNotFoundError:
                        messagebox.showerror("Homebrew Not Found", "Homebrew is not installed. Please install it first using the command below, then try again:\n\n/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
                elif os_name == "Linux":
                    messagebox.showinfo("FFmpeg Installation", "Installing FFmpeg with apt-get...")
                    subprocess.run(["sudo", "apt-get", "install", "ffmpeg", "-y"], check=True)
                    messagebox.showinfo("FFmpeg Installation", "FFmpeg installed successfully.")
                else:
                    messagebox.showerror("FFmpeg Installation", "Unsupported OS. Please install FFmpeg manually.")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("FFmpeg Installation Error", f"Error installing FFmpeg: {e}")
            except Exception as e:
                messagebox.showerror("FFmpeg Installation Error", f"An unexpected error occurred during FFmpeg installation: {e}")

    def create_widgets(self):
        # File and Playback Control Frame
        control_frame = ttk.Frame(self.main_frame, padding="10")
        control_frame.pack(pady=10)

        # Buttons
        ttk.Button(control_frame, text="Open File", command=self.open_file).pack(side="left", padx=5)
        self.play_button = ttk.Button(control_frame, text="Play", command=self.play_audio)
        self.play_button.pack(side="left", padx=5)
        self.pause_button = ttk.Button(control_frame, text="Pause", command=self.pause_audio, state="disabled")
        self.pause_button.pack(side="left", padx=5)
        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_audio, state="disabled")
        self.stop_button.pack(side="left", padx=5)
        
        # Loop Checkbox
        loop_checkbox = ttk.Checkbutton(control_frame, text="Loop Music", variable=self.loop_music_var)
        loop_checkbox.pack(side="left", padx=10)
        
        # Volume Slider
        volume_frame = ttk.Frame(control_frame)
        volume_frame.pack(side="left", padx=10)
        ttk.Label(volume_frame, text="Volume:").pack(side="left")
        self.volume_slider = ttk.Scale(volume_frame, from_=0, to=100, orient="horizontal", command=self.set_volume)
        self.volume_slider.set(50)  # Set initial volume to 50%
        self.volume_slider.pack(side="left")

        # Status Label
        self.status_label = ttk.Label(self.main_frame, text="Ready to load audio.")
        self.status_label.pack(pady=10)

        # Progress bar and time display
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(pady=10, fill="x")

        self.current_time_label = ttk.Label(self.progress_frame, text="00:00")
        self.current_time_label.pack(side="left", padx=5)

        self.progress_scale = ttk.Scale(self.progress_frame, from_=0, to=100, orient="horizontal", style="Horizontal.TScale")
        self.progress_scale.pack(side="left", fill="x", expand=True)
        self.progress_scale.bind("<ButtonRelease-1>", self.seek_audio)
        self.progress_scale.config(state="disabled")

        self.total_time_label = ttk.Label(self.progress_frame, text="00:00")
        self.total_time_label.pack(side="left", padx=5)

        # Trim Frame
        trim_frame = ttk.Frame(self.main_frame, padding="10")
        trim_frame.pack(pady=5)
        ttk.Label(trim_frame, text="Trim (seconds):").pack(side="left", padx=5)
        ttk.Label(trim_frame, text="Start:").pack(side="left", padx=5)
        self.trim_start_entry = ttk.Entry(trim_frame, width=10)
        self.trim_start_entry.pack(side="left", padx=5)
        ttk.Label(trim_frame, text="End:").pack(side="left", padx=5)
        self.trim_end_entry = ttk.Entry(trim_frame, width=10)
        self.trim_end_entry.pack(side="left", padx=5)
        ttk.Button(trim_frame, text="Trim and Play", command=self.trim_audio).pack(side="left", padx=5)

        # Save Button
        ttk.Button(self.main_frame, text="Save File", command=self.save_file).pack(pady=10)
        
        # Radio Station Button (switches to radio screen)
        radio_button = ttk.Button(self.main_frame, text="Listen to Radio", command=self.show_radio_screen)
        radio_button.pack(pady=10)
        
        # Recommendations and Library Frame
        rec_frame = ttk.Frame(self.main_frame, padding="10")
        rec_frame.pack(fill="both", expand=True, pady=10)

        # Search bar
        search_frame = ttk.Frame(rec_frame)
        search_frame.pack(fill="x", pady=5)
        ttk.Label(search_frame, text="Search Library:").pack(side="left", padx=5)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_songs)

        ttk.Label(rec_frame, text="My Library & Recommendations (based on listens):", font=("Helvetica", 12, "bold")).pack(pady=5)
        
        listbox_frame = ttk.Frame(rec_frame)
        listbox_frame.pack(fill="both", expand=True)

        self.library_listbox = tk.Listbox(listbox_frame, bg="#34495e", fg="#ecf0f1", selectbackground="#5d6d7e", font=("Helvetica", 10))
        self.library_listbox.pack(side="left", fill="both", expand=True, padx=5)
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.library_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.library_listbox.config(yscrollcommand=scrollbar.set)
        
        self.library_listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        
        # Add a button to open a dialog to remove a song
        remove_button = ttk.Button(rec_frame, text="Remove Song", command=self.ask_which_song_to_remove)
        remove_button.pack(pady=5)
        
        # Create the radio screen widgets (initially hidden)
        self.create_radio_widgets()

    def create_radio_widgets(self):
        """Creates the widgets for the radio selection screen."""
        ttk.Label(self.radio_frame, text="Select a Radio Station", font=("Helvetica", 16, "bold")).pack(pady=20)

        for station_name, data in self.radio_stations.items():
            button_frame = ttk.Frame(self.radio_frame)
            button_frame.pack(pady=10, padx=20, fill="x")
            
            # Use a lambda function to pass the station URL to the play_radio method
            ttk.Button(button_frame, text=station_name, style="Radio.TButton", command=lambda url=data["url"], name=station_name: self.play_radio(url, name)).pack(fill="x")
            ttk.Label(button_frame, text=data["description"], style="Description.TLabel", wraplength=700).pack(fill="x", padx=5, pady=2)
        
        # Back button to return to the main screen
        ttk.Button(self.radio_frame, text="Back to Main Screen", command=self.show_main_screen).pack(pady=20)

    def show_radio_screen(self):
        """Hides the main screen and shows the radio selection screen."""
        self.main_frame.pack_forget()
        self.radio_frame.pack(fill="both", expand=True)
        self.stop_audio()
        self.status_label.config(text="Select a radio station to begin streaming.")
        
    def show_main_screen(self):
        """Hides the radio screen and shows the main music library screen."""
        self.radio_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)
        self.stop_audio()
        self.status_label.config(text="Ready to load audio.")
        self.update_recommendations_listbox()
        
    def set_volume(self, value):
        """Sets the volume of the pygame mixer."""
        pygame.mixer.music.set_volume(float(value) / 100)
    
    def format_time(self, seconds):
        """Formats seconds into MM:SS format."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def update_progress(self):
        """Updates the progress bar and time labels."""
        if not self.is_playing or self.is_paused or self.is_radio:
            return
        
        # Get current playback position in milliseconds
        # Pygame returns -1 if the music has stopped
        current_pos_ms = pygame.mixer.music.get_pos()
        if current_pos_ms < 0:
            return

        current_pos_sec = current_pos_ms / 1000
        total_duration_sec = len(self.audio_segment) / 1000

        # Update the progress bar scale
        progress_percentage = (current_pos_sec / total_duration_sec) * 100 if total_duration_sec > 0 else 0
        self.progress_scale.set(progress_percentage)

        # Update the time labels
        self.current_time_label.config(text=self.format_time(current_pos_sec))
        
        # Schedule the next update
        self.after_id = self.after(100, self.update_progress)
    
    def seek_audio(self, event):
        """Seeks to a new position in the audio when the progress bar is moved."""
        if not self.is_playing or self.is_radio:
            return
        
        # Get the value from the progress scale
        progress_percentage = self.progress_scale.get()
        total_duration_ms = len(self.audio_segment)
        seek_position_ms = (progress_percentage / 100) * total_duration_ms
        
        # Pygame can't seek directly to milliseconds, so we need to reload and start at a new time
        # This is not ideal but a limitation of pygame.mixer.
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            self.audio_segment.export(temp_wav.name, format="wav")
            pygame.mixer.music.load(temp_wav.name)
            pygame.mixer.music.play(start=seek_position_ms / 1000)
            
            # Clean up temp file after it's loaded
            temp_wav.close()
            os.remove(temp_wav.name)

    def filter_songs(self, event=None):
        """Filters the songs in the listbox based on the search query."""
        query = self.search_entry.get().strip()
        if query:
            songs = self.db.search_songs(query)
        else:
            songs = self.db.get_recommendations()
            
        self.library_listbox.delete(0, tk.END)
        for path, title, play_count in songs:
            self.library_listbox.insert(tk.END, f"{title} (Listens: {play_count})")

    def on_listbox_select(self, event):
        """Plays the selected song from the listbox."""
        selection = self.library_listbox.curselection()
        if not selection:
            return
        
        selected_index = selection[0]
        # Retrieve the path from the database query result
        selected_item = self.library_listbox.get(selected_index)
        # Parse the stored string to get the path
        # Assuming format is "Title (Listens: X)"
        songs = self.db.get_recommendations()
        
        # Find the correct song path from the list of recommendations
        song_path = None
        for path, title, play_count in songs:
            if title in selected_item:
                song_path = path
                break
        
        if song_path and os.path.exists(song_path):
            self.audio_file_path = song_path
            self.status_label.config(text=f"Loading {os.path.basename(self.audio_file_path)}...")
            try:
                self.audio_segment = AudioSegment.from_file(self.audio_file_path)
                self.play_audio()
            except Exception as e:
                messagebox.showerror("Loading Error", f"Error loading file: {e}")
                self.reset_ui()
        else:
            messagebox.showerror("File Error", "File not found on disk.")
            self.reset_ui()

    def update_recommendations_listbox(self):
        """Updates the listbox with songs from the database."""
        self.library_listbox.delete(0, tk.END)
        songs = self.db.get_recommendations()
        for path, title, play_count in songs:
            self.library_listbox.insert(tk.END, f"{title} (Listens: {play_count})")

    def ask_which_song_to_remove(self):
        """Creates a new window for the user to select a song to remove."""
        top = tk.Toplevel(self)
        top.title("Remove Song")
        top.geometry("400x300")
        top.configure(bg="#2c3e50")

        frame = ttk.Frame(top, padding="10")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Select a song to remove:", font=("Helvetica", 12, "bold")).pack(pady=10)

        listbox = tk.Listbox(frame, bg="#34495e", fg="#ecf0f1", selectbackground="#5d6d7e", font=("Helvetica", 10))
        listbox.pack(fill="both", expand=True)
        
        songs = self.db.get_all_songs()
        song_paths = {}
        for path, title, play_count in songs:
            listbox.insert(tk.END, title)
            song_paths[title] = path

        def on_remove_button_click():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a song to remove.")
                return

            selected_title = listbox.get(selection[0])
            song_path_to_remove = song_paths.get(selected_title)

            if song_path_to_remove:
                if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to remove '{selected_title}' from your library?"):
                    self.db.remove_song(song_path_to_remove)
                    self.stop_audio()
                    self.update_recommendations_listbox()
                    messagebox.showinfo("Success", f"'{selected_title}' has been removed from the database.")
                    top.destroy()
            else:
                messagebox.showerror("Error", "Could not find the selected song in the database.")
        
        ttk.Button(frame, text="Remove Selected", command=on_remove_button_click).pack(pady=10)
        ttk.Button(frame, text="Cancel", command=top.destroy).pack(pady=5)

    def open_file(self):
        self.audio_file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg")]
        )
        if self.audio_file_path:
            self.status_label.config(text=f"Loading {os.path.basename(self.audio_file_path)}...")
            try:
                self.audio_segment = AudioSegment.from_file(self.audio_file_path)
                
                # Add/update the song in the database
                title = os.path.basename(self.audio_file_path)
                self.db.add_song(self.audio_file_path, title)
                self.update_recommendations_listbox()
                
                self.status_label.config(text="File loaded. Press Play to listen.")
                self.reset_ui()
                self.play_button.config(state="normal")
            except Exception as e:
                messagebox.showerror("Loading Error", f"Error loading file: {e}")
                self.reset_ui()

    def play_audio(self):
        if not self.audio_file_path:
            messagebox.showwarning("No File", "Please select an audio file first.")
            return

        self.is_playing = True
        self.is_radio = False
        
        # Increment play count for the selected song in the database
        self.db.increment_play_count(self.audio_file_path)
        self.update_recommendations_listbox()

        # Update time display and progress bar
        total_duration_sec = len(self.audio_segment) / 1000
        self.progress_scale.config(to=total_duration_sec)
        self.total_time_label.config(text=self.format_time(total_duration_sec))
        self.progress_scale.config(state="normal")
        self.update_progress()

        def play_thread():
            try:
                # Use a temporary file for pygame
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                    self.audio_segment.export(temp_wav.name, format="wav")
                    pygame.mixer.music.load(temp_wav.name)
                    
                    if self.loop_music_var.get():
                        pygame.mixer.music.play(-1)  # -1 for infinite loop
                        self.status_label.config(text=f"Playing {os.path.basename(self.audio_file_path)} (Looping)...")
                    else:
                        pygame.mixer.music.play()
                        self.status_label.config(text=f"Playing {os.path.basename(self.audio_file_path)}...")
                        
                    self.pause_button.config(state="normal")
                    self.stop_button.config(state="normal")
                    self.play_button.config(state="disabled")

            except Exception as e:
                messagebox.showerror("Playback Error", f"Error playing audio: {e}")
                self.reset_ui()

        threading.Thread(target=play_thread).start()

    def play_radio(self, url, name):
        self.stop_audio()
        
        self.status_label.config(text=f"Connecting to {name}...")
        
        self.is_radio = True
        
        # Disable progress bar for radio streams
        if self.after_id:
            self.after_cancel(self.after_id)
        self.progress_scale.set(0)
        self.current_time_label.config(text="--:--")
        self.total_time_label.config(text="--:--")
        self.progress_scale.config(state="disabled")

        def play_thread():
            try:
                # Use a requests session to handle the stream
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    
                    # Read the first chunk to get the stream started
                    first_chunk = r.raw.read(1024)
                    if not first_chunk:
                        messagebox.showerror("Radio Error", "Failed to get radio stream.")
                        return

                    # Pygame can sometimes handle direct stream-like objects, but for robustness,
                    # we will use a temp file. Note: This is not true streaming, but works for
                    # many fixed-length audio streams. For live, continuous streams,
                    # a dedicated streaming library would be better.
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                    temp_file.write(first_chunk)
                    
                    pygame.mixer.music.load(temp_file.name)
                    pygame.mixer.music.play()
                    
                    # Clean up temp file after it's loaded
                    temp_file.close()
                    os.remove(temp_file.name)
                    
                    self.is_playing = True
                    self.pause_button.config(state="normal")
                    self.stop_button.config(state="normal")
                    self.play_button.config(state="disabled")
                    self.status_label.config(text=f"Listening to {name}...")
                    self.show_main_screen()
                    
            except Exception as e:
                messagebox.showerror("Radio Error", f"Error playing radio: {e}")
                self.reset_ui()

        threading.Thread(target=play_thread).start()

    def pause_audio(self):
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.pause_button.config(text="Resume")
            self.status_label.config(text="Playback Paused.")
        elif self.is_playing and self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.pause_button.config(text="Pause")
            self.status_label.config(text="Playback Resumed.")

    def stop_audio(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.is_radio = False
        self.status_label.config(text="Playback stopped.")
        self.reset_ui()
        # Reset progress bar and time labels
        if self.after_id:
            self.after_cancel(self.after_id)
        self.progress_scale.set(0)
        self.current_time_label.config(text="00:00")
        self.total_time_label.config(text="00:00")
        self.progress_scale.config(state="disabled")

    def reset_ui(self):
        self.play_button.config(state="normal")
        self.pause_button.config(state="disabled", text="Pause")
        self.stop_button.config(state="disabled")
        
    def trim_audio(self):
        if not self.audio_segment:
            messagebox.showwarning("No File", "Please load an audio file first.")
            return

        try:
            start_sec = float(self.trim_start_entry.get())
            end_sec_text = self.trim_end_entry.get()
            
            start_ms = start_sec * 1000
            end_ms = len(self.audio_segment) if end_sec_text.lower() == "end" else float(end_sec_text) * 1000

            if start_ms >= end_ms or start_ms < 0:
                messagebox.showerror("Trim Error", "Invalid trim range. Start must be less than end.")
                return

            self.status_label.config(text="Trimming audio...")
            self.update_idletasks()

            self.audio_segment = self.audio_segment[start_ms:end_ms]
            self.status_label.config(text="Audio trimmed. Press Play to listen.")
            self.reset_ui()
            
        except ValueError:
            messagebox.showerror("Trim Error", "Invalid trim times. Please enter numbers.")

    def save_file(self):
        if not self.audio_segment:
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 File", "*.mp3"), ("WAV File", "*.wav")]
        )
        if save_path:
            self.status_label.config(text="Saving file...")
            self.update_idletasks()
            try:
                self.audio_segment.export(save_path, format=save_path.split('.')[-1])
                messagebox.showinfo("Save Status", f"File saved to: {os.path.basename(save_path)}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Error saving file: {e}")

if __name__ == "__main__":
    app = AudioStationApp()
    app.mainloop()
