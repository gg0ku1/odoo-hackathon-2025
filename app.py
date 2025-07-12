from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skill_swap.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    skills_offered = db.Column(db.String(500))
    skills_wanted = db.Column(db.String(500))
    availability = db.Column(db.String(100))
    is_public = db.Column(db.Boolean, default=False)

class Swap(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    skill_requested = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pending')

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or not all(key in data for key in ['name', 'skills_offered', 'skills_wanted', 'availability', 'is_public']):
        return jsonify({"error": "All fields (name, skills_offered, skills_wanted, availability, is_public) are required"}), 400
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
    return jsonify({"id": new_user.id, "name": new_user.name}), 201

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "name": u.name} for u in users])

@app.route('/api/swaps', methods=['POST'])
def create_swap():
    data = request.get_json()
    if not data or not all(key in data for key in ['sender_id', 'receiver_id', 'skill_requested']):
        return jsonify({"error": "All fields (sender_id, receiver_id, skill_requested) are required"}), 400
    new_swap = Swap(
        sender_id=data['sender_id'],
        receiver_id=data['receiver_id'],
        skill_requested=data['skill_requested']
    )
    db.session.add(new_swap)
    db.session.commit()
    socketio.emit('new_swap', {'id': new_swap.id, 'status': new_swap.status})
    return jsonify({"id": new_swap.id, "status": new_swap.status}), 201

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)