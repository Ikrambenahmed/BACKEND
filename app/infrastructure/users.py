from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from app.models.USERS import Users

user_bp = Blueprint("users", __name__)



