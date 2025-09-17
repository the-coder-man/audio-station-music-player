# **Audio Station**

Audio Station is a music player and manager built using Python and the tkinter library. It provides a clean and easy-to-use interface for a variety of audio tasks. Whether you want to listen to your personal music collection, discover new sounds on a live radio stream, or even do some basic audio editing, this application has you covered.

### **Prerequisites & Setup**

To get Audio Station up and running, there are a few key components you'll need to have in place. The application relies on external libraries for its core functionalities and a powerful third-party tool for audio processing.

1. **Install Python Libraries:**  
   These libraries handle everything from the user interface to file handling. You can install all of them at once using pip:  
   pip install pydub  
   pip install pygame  
   pip install requests

   * pydub is a simple and easy-to-use library for manipulating audio files.  
   * pygame provides the audio mixer, which is the heart of the playback functionality.  
   * requests is used specifically for connecting to and streaming online radio stations.  
2. **FFmpeg:**  
   FFmpeg is a versatile command-line tool that is essential for converting and processing different audio formats. When you first launch Audio Station, it will automatically check for FFmpeg. If it's not detected, the program will automatically install it depending on your operating system (Windows, macOS, or Linux). This ensures that the application can handle a wide range of audio file types without any issues.

**Note**: for windows you will have to install FFmpeg manually. This can be done by downloading the .exe file from [https://ffmpeg.org/](https://ffmpeg.org/) and running it.

### **Music Library Management**

Audio Station includes a smart, built-in music library system to help you keep track of your favorite songs. It uses a local database (music\_library.db) to store information about your audio files, so your data is saved even after you close the application.

* **Add Songs:** When you open a local audio file, the application automatically adds it to your library. It stores the file's path and title, making it easy to access again later.  
* **Remove Songs:** If you ever want to tidy up your library, you can select and remove songs from the database with just a few clicks. This action is confirmed with a pop-up to prevent accidental deletions.  
* **Recommendations:** The main library view serves as a personalized recommendation list. It automatically sorts your songs based on how many times you've listened to them, putting your most-played tracks at the top. This makes it a great way to quickly find your favorite music.  
* **Search:** A search bar is available to help you quickly find specific songs in your library. It filters the list in real-time as you type, so you don't have to scroll through your entire collection.

### **Audio Playback**

The playback controls are designed to be intuitive and easy to use, making for a seamless listening experience.

* **Supported Formats:** The player can handle popular formats like **MP3**, **WAV**, and **OGG**. When you load a file, the application will convert it to a format compatible with the mixer in the background.  
* **Basic Controls:** You have all the essential controls you'd expect: **Play**, **Pause** (which becomes **Resume** once you pause a track), and **Stop**.  
* **Looping:** The "Loop Music" checkbox allows you to set a single song to play over and over again.  
* **Volume Control:** A dedicated slider gives you fine-tuned control over the volume.  
* **Progress Bar:** The progress bar not only shows you how far along the song is, but it's also interactive. You can click anywhere on the bar to jump to a specific part of the song.

### **Audio Manipulation**

Audio Station offers simple but powerful tools for editing your audio files without needing a separate application.

* **Trimming:** You can easily trim a song to a specific section. Just enter the start and end times in seconds, and the app will isolate that part of the audio for you. This is perfect for creating ringtones or short clips from a longer track.  
* **Saving:** Once you've trimmed a file or loaded a new one, you can save it as a new audio file. The application gives you the option to choose the file format you want to save it as.

### **Live Radio Streaming**

For when you want to explore new music or news, Audio Station includes a separate screen for streaming live radio.

* **Station Selection:** The radio screen has a list of pre-configured stations for you to choose from. You can connect to popular stations like **KQED (NPR)** for news and talk, **BBC Radio 1** for the latest pop music, and **NPR News** for on-demand stories.  
* **Live Streaming:** The app connects directly to the station's live stream. The user interface switches to show that you are in radio mode and provides a brief description of the station you've selected. The progress bar is disabled for radio streams since they are continuous.

### **How to Run**

Once you have everything set up, you can run the application with a simple command in your terminal. Navigate to the folder where you've saved the Python file and enter:  
python3 "Audio station.py"  
