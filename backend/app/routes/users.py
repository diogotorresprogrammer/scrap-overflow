from flask import Blueprint, request, jsonify, abort
from ..extensions import db
from ..models import User

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


@users_bp.route('', methods=['POST'])
def create_user():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        abort(409, description='Email already registered')
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=data['password'],   # plain for now — swap for bcrypt later
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@users_bp.route('/<uuid:user_id>', methods=['GET'])
def get_user(user_id):
    user = db.get_or_404(User, user_id)
    return jsonify(user.to_dict())
