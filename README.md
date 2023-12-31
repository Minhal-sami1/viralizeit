# viralizeit

Welcome to **viralizeit**, your go-to tool for creating viral video shorts! This program empowers users to transform any YouTube link or local video file into engaging shorts by identifying potential viral segments. It utilizes advanced algorithms to extract subtitles, analyze video content, and generate shorts that are likely to capture attention.

## 📂 Project Structure
```plaintext
Viralizeit/
│
├── 📜 main.py                 # Orchestrates video downloading, processing, and shorts generation.
│
├── 📜 app.py                  # Contains all the webui for it.
│
├── 📜 subtitle_extraction.py  # Extracts subtitles from videos using the powerful auto_subtitle tool.
│
├── 📜 video_editor.py         # Leverages moviepy to edit videos, trim, and create captivating shorts.
│
├── 📜 viral_analysis.py       # Analyzes subtitles, harnessing the power of OpenAI to identify potential viral segments.
│
└── 📜 requirements.txt        # List of Python packages essential for the program.
```

## 🚀 Getting Started
### Setup & Installation
1. Clone the repository.
2. Install the required packages using: `pip install -r requirements.txt`

### Running the Program
1. Execute the `app` file.
2. Follow on-screen prompts to input either a YouTube link or the path to a local video file.
3. Specify the number of shorts you want to generate or proceed with the default.
4. Sit back as the program processes the video, extracts subtitles, identifies potential viral segments, and generates the shorts.

### Output
The shorts will be saved in a dedicated directory, each file named with start and end times of the trimmed segments.

## 📝 Note
Make sure the external command `auto_subtitle` (used for subtitle extraction) is installed on your system. It will be automatically installed when you do `pip install -r requirements.txt`

## 📢 Contributions
Feel free to fork this repository, make enhancements, and submit pull requests. All contributions are warmly welcomed! Let's make viralizeit even more amazing together. 🌟
