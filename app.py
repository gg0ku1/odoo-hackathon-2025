from flask import Flask, request, jsonify, redirect, url_for
from flask_socketio import SocketIO
from admin_routes import admin_blueprint
from models import db, User, SwapRequest  # Import from models.py

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skill_swap.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)  # Initialize db with app
socketio = SocketIO(app, cors_allowed_origins="*")

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
        return redirect(url_for('admin_dashboard'))  # Use function name directly
    return jsonify({"error": "Invalid credentials"}), 401

# Admin Dashboard Route (placeholder)
@app.route('/admin/dashboard')
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

# Register admin blueprint
app.register_blueprint(admin_blueprint, url_prefix='/admin')

# MAIN
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)