from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import firebase_admin
from firebase_admin import credentials, auth, db
import os

# Flask setup
app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Change this to something strong

# Firebase Admin setup
firebase_cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), "../../static/exam/firebase_admin.json"))
firebase_admin.initialize_app(firebase_cred, {
    'databaseURL': 'https://contact-ec611-default-rtdb.firebaseio.com/'
})

# -----------------------------
# Routes
# -----------------------------

@app.route('/')
def home():
    # If logged in -> redirect by role
    if 'user' in session:
        role = session['user'].get('role')
        if role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return render_template('exam/index.html')

# -----------------------------
# Signup / Login APIs
# -----------------------------

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    mobile = data.get('mobile')
    password = data.get('password')
    role = data.get('role', 'student')

    try:
        # Create Firebase user
        user = auth.create_user(
            email=email,
            password=password,
            display_name=name,
            phone_number=mobile if mobile else None
        )

        # Store user info in Realtime Database
        db.reference(f'users/{user.uid}').set({
            'name': name,
            'email': email,
            'mobile': mobile,
            'role': role
        })

        return jsonify({'status': 'success', 'message': 'User created successfully.'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/login', methods=['POST'])
def login():
    """
    Client will send email + password -> verify using Firebase REST API (client side or server side)
    For simplicity, assume you send ID token from Firebase front-end
    """
    data = request.json
    id_token = data.get('idToken')

    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']

        # Fetch user data
        user_data = db.reference(f'users/{uid}').get()

        # Save in Flask session (persistent until logout)
        session['user'] = user_data
        session['uid'] = uid

        return jsonify({'status': 'success', 'message': 'Login successful.', 'user': user_data})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 401


@app.route('/logout')
def logout():
    session.pop