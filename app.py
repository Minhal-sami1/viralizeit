from flask import Flask, render_template, redirect, request, session, url_for, jsonify
from Viralize.main import ViralEm
import threading, pytube
import uuid, os

app = Flask(__name__)
app.secret_key = str(uuid.uuid4().hex)

def videoShort(videoLink, request_code):
    ViralEm(key="OPENAI-API", video_id=videoLink, request_code=request_code)

@app.get('/')
def dashboard():
    files = os.listdir('./static/downloads')
    zip_files = []
    for file in files:
        if file.endswith('.zip'):
            zip_files.append("/static/downloads/"+file)
    return render_template('pages/dash.html', files=zip_files)

@app.post('/')

def dashboard_post():
    videoLink = request.form.get('vidLink')
    
    try:
        video = pytube.YouTube(videoLink)
        videoTitle = video.title
    except Exception as e:
        print(e)
        return render_template('pages/dash.html', error=f"Failed to fetch video. Error: {str(e)}")
    
    request_code = str(uuid.uuid4())
    processing_thread = threading.Thread(target=videoShort, args=(video.video_id,request_code))
    processing_thread.start()
    return render_template('pages/dash.html', msg="Success! Once ready, video will appear on this page, come back later and reload.")


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)