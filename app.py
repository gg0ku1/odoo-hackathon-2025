from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skill_swap.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    skills_offered = db.Column(db.String(500))
    skills_wanted = db.Column(db.String(500))
    availability = db.Column(db.String(100))
    is_public = db.Column(db.Boolean, default=False)

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)