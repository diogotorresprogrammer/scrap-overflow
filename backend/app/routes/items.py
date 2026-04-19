from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, asc, desc, nullslast

from ..extensions import db
from ..models import Item, LumberItem, MetalItem, FurnitureItem, ApplianceItem

items_bp = Blueprint('items', __name__, url_prefix='/api/items')

ITEM_TYPE_MAP = {
    'lumber':    LumberItem,
    'metal':     MetalItem,
    'furniture': FurnitureItem,
    'appliance': ApplianceItem,
    'item':      Item,
}

SUBCLASS_FIELDS = {
    'lumber':    ['species', 'length', 'width', 'thickness', 'grade', 'is_treated'],
    'metal':     ['metal_type', 'profile', 'length', 'width', 'thickness', 'alloy'],
    'furniture': ['furniture_type', 'material', 'style', 'num_pieces', 'has_hardware'],
    'appliance': ['appliance_type', 'brand', 'model_number', 'working_condition', 'voltage', 'amperage'],
    'item':      [],
}

BASE_FIELDS = [
    'name', 'description', 'dimension_raw', 'dimension_parsed', 'dimension_unit',
    'tags', 'location_lat', 'location_lng', 'condition', 'photo_url',
    'is_donation', 'donator_id', 'donated_at',
    'project_id', 'allocated_at', 'consumed', 'consumed_at',
]

VALID_SORTS = {'created_at', 'length', 'item_type'}


def _apply_fields(instance, data, fields):
    for field in fields:
        if field in data:
            setattr(instance, field, data[field])


@items_bp.route('', methods=['GET'])
@jwt_required()
def list_items():
    user_id = get_jwt_identity()

    item_type = request.args.get('type')
    sort      = request.args.get('sort', 'created_at')
    order     = request.args.get('order', 'desc')

    try:
        page     = max(int(request.args.get('page', 1)), 1)
        per_page = min(max(int(request.args.get('per_page', 10)), 1), 100)
    except ValueError:
        abort(400, description='page and per_page must be integers')

    if sort not in VALID_SORTS:
        sort = 'created_at'

    dir_fn = desc if order == 'desc' else asc

    if sort == 'length':
        query = (
            db.session.query(Item)
            .filter(Item.user_id == user_id)
            .outerjoin(LumberItem, Item.id == LumberItem.id)
            .outerjoin(MetalItem, Item.id == MetalItem.id)
        )
        length_col = func.coalesce(LumberItem.length, MetalItem.length)
        query = query.order_by(nullslast(dir_fn(length_col)))
    else:
        query = Item.query.filter(Item.user_id == user_id)
        sort_col = Item.item_type if sort == 'item_type' else Item.created_at
        query = query.order_by(dir_fn(sort_col))

    if item_type:
        if item_type not in ITEM_TYPE_MAP:
            abort(400, description=f"Unknown item_type '{item_type}'")
        query = query.filter(Item.item_type == item_type)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items':    [i.to_dict() for i in pagination.items],
        'total':    pagination.total,
        'page':     pagination.page,
        'per_page': pagination.per_page,
        'pages':    pagination.pages,
    })


@items_bp.route('', methods=['POST'])
@jwt_required()
def create_item():
    user_id = get_jwt_identity()
    data = request.get_json()

    item_type = data.get('item_type', 'item')
    if item_type not in ITEM_TYPE_MAP:
        abort(400, description=f"Unknown item_type '{item_type}'")

    cls = ITEM_TYPE_MAP[item_type]
    item = cls(item_type=item_type, user_id=user_id, name=data['name'])

    _apply_fields(item, data, BASE_FIELDS)
    _apply_fields(item, data, SUBCLASS_FIELDS[item_type])

    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@items_bp.route('/<uuid:item_id>', methods=['GET'])
@jwt_required()
def get_item(item_id):
    user_id = get_jwt_identity()
    item = db.get_or_404(Item, item_id)
    if str(item.user_id) != user_id:
        abort(403)
    return jsonify(item.to_dict())


@items_bp.route('/<uuid:item_id>', methods=['PATCH'])
@jwt_required()
def update_item(item_id):
    user_id = get_jwt_identity()
    item = db.get_or_404(Item, item_id)
    if str(item.user_id) != user_id:
        abort(403)

    data = request.get_json()
    _apply_fields(item, data, BASE_FIELDS)
    _apply_fields(item, data, SUBCLASS_FIELDS.get(item.item_type, []))

    db.session.commit()
    return jsonify(item.to_dict())


@items_bp.route('/<uuid:item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    user_id = get_jwt_identity()
    item = db.get_or_404(Item, item_id)
    if str(item.user_id) != user_id:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    return '', 204
