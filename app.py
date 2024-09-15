from flask import Flask, render_template, Response, request, jsonify, redirect, url_for, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import cv2
from fer import FER
import google.generativeai as genai
import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.objectid import ObjectId

# Configure the API key for Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Initialize the generative model
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_default_secret_key')  # Use environment variable for security

# Initialize FER detector
detector = FER()

camera = None  # Initialize the camera variable

# MongoDB setup
mongo_uri = 'mongodb://localhost:27017'
client = MongoClient(mongo_uri)
db = client['chat_history']
collection = db['History']
users = db['Users']  # User collection
feedback_collection = db['Feedback']  # Feedback collection

import os

def send_confirmation_email(email, name):
    sender_email = os.environ.get('EMAIL_ADDRESS')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    receiver_email = email

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Feedback Confirmation"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    text = f"Hi {name},\n\nThank you for your feedback!\n\nBest regards,\nTeam"
    html = f"""
    <html>
    <body>
        <p>Hi {name},</p>
        <p>Thank you for your feedback!</p>
        <p>Best regards,<br>Team Bhavana</p>
    </body>
    </html>
    """
    
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print(f'Email sent to {email}')
    except Exception as e:
        print(f"Failed to send email: {str(e)}")


@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    name = request.form['name']
    email = request.form['email']
    feedback = request.form['feedback']
    star_rating = request.form.get('star')  # Capture the star rating

    # Store feedback in MongoDB
    feedback_data = {
        'name': name,
        'email': email,
        'feedback': feedback,
        'star_rating': star_rating,
        'timestamp': datetime.now()
    }
    feedback_collection.insert_one(feedback_data)

    # Send confirmation email
    send_confirmation_email(email, name)

    return redirect(url_for('about'))

def start_camera():
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)

def stop_camera():
    global camera
    if camera is not None and camera.isOpened():
        camera.release()

def generate_frames():
    global camera
    start_camera()  # Ensure the camera is started
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Detect emotions in the frame
            emotion_data = detector.detect_emotions(frame)
            if emotion_data:
                for face in emotion_data:
                    (x, y, w, h) = face['box']
                    emotion_dict = face['emotions']
                    emotion, _ = max(emotion_dict.items(), key=lambda item: item[1])
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, f'{emotion}', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('home'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users.find_one({'username': username}):
            return render_template('signup.html', error='Username already exists')
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        users.insert_one({'username': username, 'password': hashed_password})
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/frozen_frame')
def frozen_frame():
    global camera
    success, frame = camera.read()
    if success:
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        return Response(
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n',
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    return '', 204  # No content


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture_emotion', methods=['POST'])
def capture_emotion():
    global camera, captured_frame
    success, frame = camera.read()
    if success:
        # Save the captured frame to a file
        captured_frame_path = 'static/captured_frame.jpg'
        cv2.imwrite(captured_frame_path, frame)
        captured_frame = captured_frame_path
        
        emotion_data = detector.detect_emotions(frame)
        if emotion_data:
            face = emotion_data[0]
            emotion_dict = face['emotions']
            detected_emotion, _ = max(emotion_dict.items(), key=lambda item: item[1])
            return jsonify({"captured_emotion": detected_emotion})
    return jsonify({"captured_emotion": "neutral"})

@app.route('/chatbot_response', methods=['POST'])
def chatbot_response():
    data = request.json
    user_name = session.get('username', 'User')  # Use session username
    detected_emotion = data.get('detected_emotion', 'neutral')
    user_input = data.get('user_input', '').lower()
    chat_id = data.get('chat_id')

    if user_input == '':
        prompt = f"Generate a friendly and super excited message from a chatbot named Bhavana. The user is named {user_name} and is feeling {detected_emotion}. Please engage the user warmly."
    else:
        prompt = (f"Generate an enthusiastic and excited response from a chatbot named Bhavana based on the user's emotion, which is {detected_emotion}. "
                  f"The user has said: '{user_input}'. The response should be lively, conversational, and tailored to the user's current emotional state.")

    response = model.generate_content(prompt)
    response_text = response.text.strip()

    # Update chat history in MongoDB
    timestamp = datetime.now()

    if chat_id:
        collection.update_one(
            {'_id': ObjectId(chat_id)},
            {'$push': {'chat_history': {
                'timestamp': timestamp,
                'user_input': user_input,
                'response': response_text
            }}}
        )
    else:
        chat_entry = {
            'timestamp': timestamp,
            'user_name': user_name,
            'detected_emotion': detected_emotion,
            'chat_history': [
                {
                    'timestamp': timestamp,
                    'user_input': user_input,
                    'response': response_text
                }
            ]
        }
        result = collection.insert_one(chat_entry)
        chat_id = str(result.inserted_id)

    return jsonify({"response": response_text, "chat_id": chat_id})

@app.route('/new_chat', methods=['POST'])
def new_chat():
    start_camera()  # Reactivate the camera for the new chat
    return jsonify({"status": "new_chat_started"})

@app.route('/chat_history', methods=['GET'])
def chat_history():
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    last_week = now - timedelta(days=7)

    user_name = session.get('username')  # Get the username from the session
    if not user_name:
        return jsonify({"status": "error", "message": "User not logged in"}), 401

    history = collection.aggregate([
        {"$match": {"user_name": user_name}},  # Filter by username
        {"$unwind": "$chat_history"},
        {"$group": {
            "_id": {
                "chat_id": "$_id",
                "emotion": "$detected_emotion",
                "time_class": {
                    "$cond": [
                        {"$eq": [{"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}, now.strftime("%Y-%m-%d")]},
                        "Today",
                        {
                            "$cond": [
                                {"$eq": [{"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}, yesterday.strftime("%Y-%m-%d")]},
                                "Yesterday",
                                {"$cond": [{"$gte": ["$timestamp", last_week]}, "Previous 7 Days", "Older"]}
                            ]
                        }
                    ]
                }
            },
            "first_message": {"$first": "$chat_history.user_input"},
            "chat_count": {"$sum": 1}
        }},
        {"$sort": {"_id.time_class": -1, "_id.chat_id": -1}}  # Sort by timeline descending
    ])
    history_list = list(history)
    for h in history_list:
        h['_id']['chat_id'] = str(h['_id']['chat_id'])
    return jsonify(history_list)

@app.route('/load_chat/<chat_id>', methods=['GET'])
def load_chat(chat_id):
    chat = collection.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        return jsonify({"status": "error", "message": "Chat not found"}), 404

    return jsonify({
        "_id": {"$oid": str(chat['_id'])},
        "chat_history": chat.get("chat_history", [])
    })

# Define routes for other modules
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/bhavana')
def bhavana():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('bhavana.html')

@app.route('/self_assessment')
def self_assessment():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('self_assessment.html')

@app.route('/feedback')
def articles():
    return render_template('feedback.html')

@app.route('/stress')
def stress():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('stress.html')

@app.route('/anxiety')
def anxiety():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('anxiety.html')

@app.route('/depression')
def depression():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('depression.html')

@app.route('/login_signup')
def login_signup():
    return redirect(url_for('login'))

if __name__ == "__main__":
    print(app.url_map)
    app.run(debug=True)