from flask import Blueprint, jsonify, request
from models import db, User, SwapRequest

admin_blueprint = Blueprint('admin', __name__)

# Ban a user
@admin_blueprint.route('/ban/<string:user_id>', methods=['POST'])
def ban_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User {user_id} banned successfully"}), 200

# Reject inappropriate skill descriptions
@admin_blueprint.route('/review/<string:user_id>', methods=['PUT'])
def review_user_skills(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    user.skills_offered = []
    user.skills_wanted = []
    db.session.commit()
    return jsonify({"message": f"Skills for user {user_id} cleared"}), 200

# Monitor swaps by status
@admin_blueprint.route('/swaps', methods=['GET'])
def monitor_swaps():
    status = request.args.get('status')  
    query = SwapRequest.query
    if status:
        query = query.filter_by(status=status)
    swaps = query.all()
    return jsonify([s.to_dict() for s in swaps]), 200

# Send platform-wide message (dummy endpoint for now)
@admin_blueprint.route('/messages', methods=['POST'])
def send_message():
    data = request.get_json()
    message = data.get('message')
    if not message:
        return jsonify({"error": "Message is required"}), 400
    return jsonify({"message": f"Broadcast sent: {message}"}), 200

# Download reports
@admin_blueprint.route('/report', methods=['GET'])
def download_report():
    users = User.query.all()
    swaps = SwapRequest.query.all()
    return jsonify({
        "users": [u.to_dict() for u in users],
        "swaps": [s.to_dict() for s in swaps]
    }), 200
