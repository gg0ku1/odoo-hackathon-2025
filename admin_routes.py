from flask import Blueprint, jsonify, request
from models import db, User, SwapRequest  # Import from models.py

admin_blueprint = Blueprint('admin', __name__)

# Ban a user by ID 
@admin_blueprint.route('/ban/<string:user_id>', methods=['POST'])
def ban_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"✅ User {user_id} has been banned"}), 200

# Clear a user's skills (reject spam descriptions)
@admin_blueprint.route('/review/<string:user_id>', methods=['PUT'])
def clear_user_skills(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    user.skills_offered = ""
    user.skills_wanted = ""
    db.session.commit()
    return jsonify({"message": f"✅ Cleared skills for user {user_id}"}), 200

# Monitor swaps 
@admin_blueprint.route('/swaps', methods=['GET'])
def monitor_swaps():
    status = request.args.get('status')
    query = SwapRequest.query
    if status:
        query = query.filter_by(status=status)
    swaps = query.all()
    return jsonify([s.to_dict() for s in swaps]), 200

# Send platform-wide message 
@admin_blueprint.route('/broadcast', methods=['POST'])
def broadcast_message():
    data = request.get_json()
    message = data.get('message')
    if not message:
        return jsonify({"error": "Message is required"}), 400
    # NOTE: Could integrate SocketIO emit here for real broadcast
    return jsonify({"message": f"📣 Broadcast sent: {message}"}), 200

# Download full report of users and swaps
@admin_blueprint.route('/report', methods=['GET'])
def download_report():
    users = User.query.all()
    swaps = SwapRequest.query.all()
    return jsonify({
        "users": [u.to_dict() for u in users],
        "swaps": [s.to_dict() for s in swaps]
    }), 200