from flask import Blueprint, request, jsonify, abort
from ..extensions import db
from ..models import Item, LumberItem, MetalItem, FurnitureItem, ApplianceItem

items_bp = Blueprint('items', __name__, url_prefix='/api/items')

# Maps item_type string → model class
ITEM_TYPE_MAP = {
    'lumber':    LumberItem,
    'metal':     MetalItem,
    'furniture': FurnitureItem,
    'appliance': ApplianceItem,
    'item':      Item,
}

# Fields accepted per subclass on create/update
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


def _apply_fields(instance, data, fields):
    for field in fields:
        if field in data:
            setattr(instance, field, data[field])


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------

@items_bp.route('', methods=['GET'])
def list_items():
    item_type = request.args.get('type')
    user_id = request.args.get('user_id')

    query = Item.query

    if item_type:
        if item_type not in ITEM_TYPE_MAP:
            abort(400, description=f"Unknown item_type '{item_type}'")
        query = query.filter(Item.item_type == item_type)

    if user_id:
        query = query.filter(Item.user_id == user_id)

    items = query.order_by(Item.created_at.desc()).all()
    return jsonify([i.to_dict() for i in items])


@items_bp.route('', methods=['POST'])
def create_item():
    data = request.get_json()

    item_type = data.get('item_type', 'item')
    if item_type not in ITEM_TYPE_MAP:
        abort(400, description=f"Unknown item_type '{item_type}'")

    cls = ITEM_TYPE_MAP[item_type]
    item = cls(item_type=item_type, user_id=data['user_id'], name=data['name'])

    _apply_fields(item, data, BASE_FIELDS)
    _apply_fields(item, data, SUBCLASS_FIELDS[item_type])

    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


# ---------------------------------------------------------------------------
# Single item
# ---------------------------------------------------------------------------

@items_bp.route('/<uuid:item_id>', methods=['GET'])
def get_item(item_id):
    item = db.get_or_404(Item, item_id)
    return jsonify(item.to_dict())


@items_bp.route('/<uuid:item_id>', methods=['PATCH'])
def update_item(item_id):
    item = db.get_or_404(Item, item_id)
    data = request.get_json()

    _apply_fields(item, data, BASE_FIELDS)
    _apply_fields(item, data, SUBCLASS_FIELDS.get(item.item_type, []))

    db.session.commit()
    return jsonify(item.to_dict())


@items_bp.route('/<uuid:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = db.get_or_404(Item, item_id)
    db.session.delete(item)
    db.session.commit()
    return '', 204
