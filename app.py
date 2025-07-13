from flask import Flask, request, jsonify, redirect, url_for, render_template, session
from flask_socketio import SocketIO
from flask_cors import CORS
from admin_routes import admin_blueprint
from models import db, User, SwapRequest
from flask import send_from_directory
import os
from functools import wraps

app = Flask(__name__, template_folder='frontend')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skill_swap.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)  # Add a secret key for sessions
CORS(app)  # Enable CORS for all routes
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({"error": "Admin access required"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    users = User.query.all()
    
    # Extract unique skills from users' skills
    all_skills = set()
    for user in users:
        if user.skills_offered:
            all_skills.update(skill.strip() for skill in user.skills_offered.split(','))
        if user.skills_wanted:
            all_skills.update(skill.strip() for skill in user.skills_wanted.split(','))
    
    # Extract unique locations
    locations = set(user.location for user in users if user.location)
    
    return render_template(
        'homepage.html',
        users=[u.to_dict() for u in users],
        skills=sorted(all_skills),
        locations=sorted(locations),
        stats={}
    )

# ROUTES
@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or not all(key in data for key in ['name', 'skills_offered', 'skills_wanted', 'availability', 'is_public']):
        return jsonify({"error": "All fields are required"}), 400
    new_user = User(
        name=data['name'],
        location=data.get('location'),
        skills_offered=data['skills_offered'],
        skills_wanted=data['skills_wanted'],
        availability=data['availability'],
        is_public=data['is_public']
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.to_dict()), 201

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

@app.route('/api/swaps', methods=['POST'])
def create_swap():
    data = request.get_json()
    if not data or not all(key in data for key in ['sender_id', 'receiver_id', 'skill_requested']):
        return jsonify({"error": "All fields are required"}), 400
    new_swap = SwapRequest(
        sender_id=data['sender_id'],
        receiver_id=data['receiver_id'],
        skill_requested=data['skill_requested']
    )
    db.session.add(new_swap)
    db.session.commit()
    socketio.emit('new_swap', new_swap.to_dict())
    return jsonify(new_swap.to_dict()), 201

@app.route('/api/swaps', methods=['GET'])
def list_swaps():
    sender_id = request.args.get('sender_id')
    receiver_id = request.args.get('receiver_id')
    query = SwapRequest.query
    if sender_id:
        query = query.filter_by(sender_id=sender_id)
    if receiver_id:
        query = query.filter_by(receiver_id=receiver_id)
    swaps = query.all()
    return jsonify([s.to_dict() for s in swaps])

@app.route('/api/swaps/<string:swap_id>', methods=['PUT'])
def update_swap(swap_id):
    swap = SwapRequest.query.get_or_404(swap_id)
    new_status = request.json.get("status")
    if new_status not in ["pending", "accepted", "rejected"]:
        return jsonify({"error": "Invalid status"}), 400
    swap.status = new_status
    db.session.commit()
    socketio.emit('swap_update', swap.to_dict())
    return jsonify(swap.to_dict()), 200

@app.route('/api/swaps/<string:swap_id>', methods=['DELETE'])
def delete_swap(swap_id):
    swap = SwapRequest.query.get_or_404(swap_id)
    db.session.delete(swap)
    db.session.commit()
    return jsonify({"message": f"Swap {swap_id} deleted"}), 200

# Admin Login Route
@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    admin_username = data.get('username')
    admin_password = data.get('password')
    if admin_username == "admin" and admin_password == "admin123":
        session['admin_logged_in'] = True  # Set session variable
        return redirect(url_for('admin_dashboard'))  # Use function name directly
    return jsonify({"error": "Invalid credentials"}), 401

# Admin Dashboard Route (placeholder)
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return jsonify({
        "message": "Welcome to Admin Dashboard",
        "actions": [
            "/admin/ban/<user_id>",
            "/admin/review/<user_id>",
            "/admin/swaps?status=<status>",
            "/admin/broadcast",
            "/admin/report"
        ]
    })

# Serve admin page
@app.route('/admin')
def admin_page():
    return send_from_directory('.', 'admin.html')

# User authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        # Add your login logic here
        session['user_id'] = 1  # Set this to actual user id after authentication
        return jsonify({"message": "Login successful"})
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        # Add your signup logic here
        return jsonify({"message": "Signup successful"})
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    # Add your profile page logic here
    return render_template('userprofile.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    # Add your dashboard logic here
    return jsonify({"message": "Dashboard"})

# Register admin blueprint
app.register_blueprint(admin_blueprint, url_prefix='/admin')

# MAIN
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)