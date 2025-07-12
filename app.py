from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skill_swap.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# MODELS
class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    skills_offered = db.Column(db.String(500))  # Changed back to String
    skills_wanted = db.Column(db.String(500))   # Changed back to String
    availability = db.Column(db.String(100))
    is_public = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "skills_offered": self.skills_offered,
            "skills_wanted": self.skills_wanted,
            "availability": self.availability,
            "is_public": self.is_public
        }

class SwapRequest(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    skill_requested = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "skill_requested": self.skill_requested,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }

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

# MAIN
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)