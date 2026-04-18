from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone

from ..extensions import db
from ..models import Project

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')

BASE_FIELDS = ['name', 'description', 'status', 'completed_at']


@projects_bp.route('', methods=['GET'])
@jwt_required()
def list_projects():
    user_id = get_jwt_identity()
    projects = (
        Project.query
        .filter(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
        .all()
    )
    return jsonify([p.to_dict() for p in projects])


@projects_bp.route('', methods=['POST'])
@jwt_required()
def create_project():
    user_id = get_jwt_identity()
    data = request.get_json()
    project = Project(user_id=user_id, name=data['name'])
    project.description = data.get('description')
    project.status = data.get('status', 'planning')
    db.session.add(project)
    db.session.commit()
    return jsonify(project.to_dict()), 201


@projects_bp.route('/<uuid:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    user_id = get_jwt_identity()
    project = db.get_or_404(Project, project_id)
    if str(project.user_id) != user_id:
        abort(403)
    return jsonify(project.to_dict())


@projects_bp.route('/<uuid:project_id>', methods=['PATCH'])
@jwt_required()
def update_project(project_id):
    user_id = get_jwt_identity()
    project = db.get_or_404(Project, project_id)
    if str(project.user_id) != user_id:
        abort(403)

    data = request.get_json()
    for field in BASE_FIELDS:
        if field in data:
            setattr(project, field, data[field])

    # auto-stamp completed_at when status flips to completed
    if data.get('status') == 'completed' and not project.completed_at:
        project.completed_at = datetime.now(timezone.utc)

    db.session.commit()
    return jsonify(project.to_dict())


@projects_bp.route('/<uuid:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    user_id = get_jwt_identity()
    project = db.get_or_404(Project, project_id)
    if str(project.user_id) != user_id:
        abort(403)
    db.session.delete(project)
    db.session.commit()
    return '', 204
