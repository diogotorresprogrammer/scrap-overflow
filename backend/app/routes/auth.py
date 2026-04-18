from flask import Blueprint, request, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

from ..extensions import db
from ..models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        abort(409, description='Email already registered')
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
    )
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity=str(user.id))
    return jsonify({'access_token': token, 'user': user.to_dict()}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        abort(401, description='Invalid email or password')
    token = create_access_token(identity=str(user.id))
    return jsonify({'access_token': token, 'user': user.to_dict()})
