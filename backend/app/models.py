import uuid
from decimal import Decimal

from sqlalchemy import Column, String, Text, Float, DateTime, JSON, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .extensions import db


class BaseModel(db.Model):
    __abstract__ = True

    _default_fields = []
    _hidden_fields = []
    _readonly_fields = []

    def to_dict(self, show=None, _hide=None, _path=None):
        show = show or []
        _hide = _hide or []

        if _path is None:
            _path = self.__tablename__

        columns = {c.key for c in self.__mapper__.columns}
        relationships = {r.key for r in self.__mapper__.relationships}
        hybrid_props = {
            k for k in dir(type(self))
            if isinstance(getattr(type(self), k), hybrid_property)
        }

        visible = set(self._default_fields) | (columns - set(self._hidden_fields) - set(_hide))
        for field in show:
            if field.split('.')[0] in relationships:
                visible.add(field)

        result = {}
        for key in visible:
            if key in self._hidden_fields and key not in show:
                continue
            if key in columns:
                val = getattr(self, key)
                if hasattr(val, 'isoformat'):
                    result[key] = val.isoformat()
                elif isinstance(val, Decimal):
                    result[key] = float(val)
                elif isinstance(val, uuid.UUID):
                    result[key] = str(val)
                else:
                    result[key] = val
            elif key in hybrid_props:
                result[key] = getattr(self, key)
            elif key in relationships:
                rel = getattr(self, key)
                rel_path = f"{_path}.{key}"
                if rel is None:
                    result[key] = None
                elif hasattr(rel, '__iter__'):
                    nested_show = [f.split('.', 1)[1] for f in show if f.startswith(f"{key}.")]
                    result[key] = [
                        r.to_dict(show=nested_show, _path=rel_path)
                        if hasattr(r, 'to_dict') else str(r)
                        for r in rel
                    ]
                else:
                    nested_show = [f.split('.', 1)[1] for f in show if f.startswith(f"{key}.")]
                    result[key] = (
                        rel.to_dict(show=nested_show, _path=rel_path)
                        if hasattr(rel, 'to_dict') else str(rel)
                    )

        return result


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(BaseModel):
    __tablename__ = 'users'

    _default_fields = ['id', 'username', 'email', 'created_at']
    _hidden_fields = ['password_hash']
    _readonly_fields = ['id', 'created_at']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(200), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())

    items = relationship('Item', back_populates='user', lazy='dynamic')
    projects = relationship('Project', back_populates='user', lazy='dynamic')
    donators = relationship('Donator', back_populates='user', lazy='dynamic')


# ---------------------------------------------------------------------------
# Donator
# ---------------------------------------------------------------------------

class Donator(BaseModel):
    __tablename__ = 'donators'

    _default_fields = ['id', 'user_id', 'name', 'contact', 'notes', 'created_at']
    _hidden_fields = []
    _readonly_fields = ['id', 'created_at']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    name = Column(String(200), nullable=False)
    # free-form: email, phone, social handle, etc.
    contact = Column(String(200))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())

    user = relationship('User', back_populates='donators')
    items = relationship('Item', back_populates='donator', lazy='dynamic')


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

class Project(BaseModel):
    __tablename__ = 'projects'

    _default_fields = [
        'id', 'user_id', 'name', 'description', 'status', 'created_at', 'completed_at',
    ]
    _hidden_fields = []
    _readonly_fields = ['id', 'created_at']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    # planning | in_progress | completed | cancelled
    status = Column(String(50), nullable=False, default='planning')
    created_at = Column(DateTime(timezone=True), default=func.now())
    completed_at = Column(DateTime(timezone=True))

    user = relationship('User', back_populates='projects')
    # Items from inventory allocated to this project
    items = relationship('Item', back_populates='project', lazy='dynamic')
    # Planned requirements — may or may not be matched to inventory items yet
    required_items = relationship('ProjectItem', back_populates='project', lazy='dynamic')


# ---------------------------------------------------------------------------
# ProjectItem — a planned requirement; matched to an inventory Item when found
# ---------------------------------------------------------------------------

class ProjectItem(BaseModel):
    __tablename__ = 'project_items'

    _default_fields = [
        'id', 'project_id', 'item_type', 'name', 'notes', 'quantity',
        'status', 'matched_item_id', 'matched_at', 'created_at',
    ]
    _hidden_fields = []
    _readonly_fields = ['id', 'created_at']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)

    # What category of item is needed (lumber, metal, furniture, appliance, or left blank)
    item_type = Column(String(50))
    name = Column(String(200), nullable=False)
    notes = Column(Text)
    quantity = Column(Integer, nullable=False, default=1)

    # needed | matched | fulfilled
    # needed    — no inventory item assigned yet
    # matched   — linked to an inventory item, project still running
    # fulfilled — project completed and item was consumed
    status = Column(String(50), nullable=False, default='needed')

    # Filled once an inventory item is matched to this requirement
    matched_item_id = Column(UUID(as_uuid=True), ForeignKey('items.id'), nullable=True)
    matched_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), default=func.now())

    project = relationship('Project', back_populates='required_items')
    matched_item = relationship('Item', foreign_keys=[matched_item_id])


# ---------------------------------------------------------------------------
# Item base (joined-table inheritance)
# ---------------------------------------------------------------------------

class Item(BaseModel):
    __tablename__ = 'items'

    _default_fields = [
        'id', 'user_id', 'item_type', 'name', 'description', 'dimension_raw', 'dimension_parsed',
        'dimension_unit', 'tags', 'location', 'condition', 'photo_url', 'created_at',
        'is_donation', 'donator_id', 'donated_at',
        'allocated', 'project_id', 'allocated_at', 'consumed', 'consumed_at',
    ]
    _hidden_fields = ['location_lat', 'location_lng']
    _readonly_fields = ['id', 'created_at']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    item_type = Column(String(50), nullable=False)

    name = Column(String(200), nullable=False)
    description = Column(Text)
    dimension_raw = Column(String(100))
    dimension_parsed = Column(JSON)
    # Unit that applies to all dimension columns on subclasses — default mm
    dimension_unit = Column(String(10), nullable=False, default='mm')
    tags = Column(JSON, default=list)
    location_lat = Column(Float)
    location_lng = Column(Float)
    condition = Column(String(50))
    photo_url = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Donation
    is_donation = Column(Boolean, nullable=False, default=False)
    donator_id = Column(UUID(as_uuid=True), ForeignKey('donators.id'), nullable=True)
    donated_at = Column(DateTime(timezone=True))

    # Allocation — set when item is assigned to a project
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=True)
    allocated_at = Column(DateTime(timezone=True))

    # Consumption — set when the item has been fully used up in a completed project
    consumed = Column(Boolean, nullable=False, default=False)
    consumed_at = Column(DateTime(timezone=True))

    user = relationship('User', back_populates='items')
    donator = relationship('Donator', back_populates='items')
    project = relationship('Project', back_populates='items')

    __mapper_args__ = {
        'polymorphic_on': item_type,
        'polymorphic_identity': 'item',
    }

    @hybrid_property
    def location(self):
        if self.location_lat is None or self.location_lng is None:
            return None
        return {'lat': self.location_lat, 'lng': self.location_lng}

    @hybrid_property
    def allocated(self):
        return self.project_id is not None


# ---------------------------------------------------------------------------
# Subclasses
# ---------------------------------------------------------------------------

class LumberItem(Item):
    __tablename__ = 'lumber_items'

    _default_fields = Item._default_fields + [
        'species', 'length', 'width', 'thickness', 'grade', 'is_treated',
    ]

    id = Column(UUID(as_uuid=True), ForeignKey('items.id'), primary_key=True)

    # e.g. pine, oak, douglas fir, poplar
    species = Column(String(100))
    length = Column(Float)
    width = Column(Float)
    thickness = Column(Float)
    # e.g. #1, #2, select structural, common
    grade = Column(String(50))
    is_treated = Column(Boolean, default=False)

    __mapper_args__ = {'polymorphic_identity': 'lumber'}


class MetalItem(Item):
    __tablename__ = 'metal_items'

    _default_fields = Item._default_fields + [
        'metal_type', 'profile', 'length', 'width', 'thickness', 'alloy',
    ]

    id = Column(UUID(as_uuid=True), ForeignKey('items.id'), primary_key=True)

    # e.g. steel, aluminum, copper, cast iron, stainless
    metal_type = Column(String(100))
    # e.g. flat bar, angle, tube, pipe, sheet, rod, I-beam, channel
    profile = Column(String(100))
    length = Column(Float)
    width = Column(Float)
    thickness = Column(Float)
    # e.g. 6061, 304, A36, 1018
    alloy = Column(String(50))

    __mapper_args__ = {'polymorphic_identity': 'metal'}


class FurnitureItem(Item):
    __tablename__ = 'furniture_items'

    _default_fields = Item._default_fields + [
        'furniture_type', 'material', 'style', 'num_pieces', 'has_hardware',
    ]

    id = Column(UUID(as_uuid=True), ForeignKey('items.id'), primary_key=True)

    # e.g. chair, table, dresser, cabinet, sofa, bookshelf, bed frame
    furniture_type = Column(String(100))
    # e.g. solid wood, plywood, metal, upholstered, mixed
    material = Column(String(100))
    # e.g. mid-century, industrial, rustic, contemporary
    style = Column(String(100))
    num_pieces = Column(Integer, default=1)
    has_hardware = Column(Boolean, default=False)

    __mapper_args__ = {'polymorphic_identity': 'furniture'}


class ApplianceItem(Item):
    __tablename__ = 'appliance_items'

    _default_fields = Item._default_fields + [
        'appliance_type', 'brand', 'model_number', 'working_condition', 'voltage', 'amperage',
    ]

    id = Column(UUID(as_uuid=True), ForeignKey('items.id'), primary_key=True)

    # e.g. refrigerator, washer, dryer, stove, dishwasher, water heater, HVAC
    appliance_type = Column(String(100))
    brand = Column(String(100))
    model_number = Column(String(100))
    # working | unknown | for-parts
    working_condition = Column(String(50))
    voltage = Column(Integer)   # 110 or 220
    amperage = Column(Float)    # e.g. 15.0, 20.0, 30.0

    __mapper_args__ = {'polymorphic_identity': 'appliance'}
