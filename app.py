import random
import os
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func
from dotenv import load_dotenv
from models import db, Voice, TestResult
from elo_rankings import calculate_updated_ratings, get_targeted_voices

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Ensure the instance folder exists for the database
os.makedirs(app.instance_path, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'tts_testing.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-local-testing')

db.init_app(app)

csrf = CSRFProtect(app)

def get_client_ip():
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.remote_addr


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Fix #8: Use session to retrieve voice names
        voice_a_name = session.get('voice_a')
        voice_b_name = session.get('voice_b')
        choice_label = request.form.get('choice') # 'A' or 'B'
        
        if voice_a_name and voice_b_name and choice_label:
            chosen_voice_name = voice_a_name if choice_label == 'A' else voice_b_name

            # Fix #7: Simple cooldown check (1 minute)
            last_vote = TestResult.query.filter_by(
                ip_address=get_client_ip(),
                voice_a_name=voice_a_name,
                voice_b_name=voice_b_name
            ).order_by(TestResult.timestamp.desc()).first()
            
            if last_vote and (datetime.now(timezone.utc) - last_vote.timestamp.replace(tzinfo=timezone.utc)
                              < timedelta(minutes=1)):
                return "Please wait a minute before voting on the same pair again.", 429

            # Record the result
            result = TestResult(
                ip_address=get_client_ip(),
                voice_a_name=voice_a_name,
                voice_b_name=voice_b_name,
                chosen_voice_name=chosen_voice_name
            )
            db.session.add(result)
            
            # Update Elo ratings
            voice_a = Voice.query.filter_by(name=voice_a_name).first()
            voice_b = Voice.query.filter_by(name=voice_b_name).first()
            
            if voice_a and voice_b:
                calculate_updated_ratings(voice_a, voice_b, chosen_voice_name)
            
            db.session.commit()
            
            # Store last pair so next trial excludes them, then clear current pair
            session['last_voices'] = [voice_a_name, voice_b_name]
            session.pop('voice_a', None)
            session.pop('voice_b', None)

            return redirect(url_for('index'))

    # GET request
    voices = Voice.query.all()
    
    # Fix #4: Replace full table scan with aggregating SQL queries
    pair_counts = db.session.query(
        TestResult.voice_a_name, TestResult.voice_b_name
    ).distinct().all()
    tested_pairs = {f"{a}-{b}" for a, b in pair_counts}
    
    counts_a = db.session.query(
        TestResult.voice_a_name, func.count()
    ).group_by(TestResult.voice_a_name).all()
    counts_b = db.session.query(
        TestResult.voice_b_name, func.count()
    ).group_by(TestResult.voice_b_name).all()
    
    voice_test_counts = {name: c for name, c in counts_a}
    for name, c in counts_b:
        voice_test_counts[name] = voice_test_counts.get(name, 0) + c
    
    last_voices = session.pop('last_voices', None)
    current_voices = get_targeted_voices(voices, tested_pairs, voice_test_counts, exclude=last_voices)
    
    # Fix #8: Store voice names in session
    session['voice_a'] = current_voices[0].name
    session['voice_b'] = current_voices[1].name
    
    # Randomly select a voice to auto-play (A or B)
    auto_play_voice = random.choice(['A', 'B'])
    # Random starting position percentage (between 0 and 70%)
    random_start_percent = random.randint(0, 70)
    
    return render_template('index.html', 
                           current_voices=current_voices,
                           auto_play_voice=auto_play_voice,
                           random_start_percent=random_start_percent)

@app.route('/results')
def results():
    min_matches = 3
    rankings = Voice.query.filter(Voice.matches >= min_matches).order_by(Voice.rating.desc()).all()
    return render_template('results.html', rankings=rankings, min_matches=min_matches)

@app.route('/voices')
def voices_directory():
    all_voices = Voice.query.order_by(Voice.name.asc()).all()
    return render_template('voices.html', voices=all_voices)

if __name__ == '__main__':
    db.init_app(app)
    with app.app_context():
        db.create_all()
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=8000)
