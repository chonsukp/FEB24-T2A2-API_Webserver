from datetime import timedelta

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from init import db
from models.domain import Domain, domain_schema, domains_schema
from models.service import Service, services_schema
from models.domain_service import Domain_Service, domain_service_schema, domain_services_schema

domains_bp = Blueprint("domains", __name__, url_prefix="/domains")

@domains_bp.route("/")
def get_all_domains():
    stmt = db.select(Domain)
    domains = db.session.scalars(stmt)  
    return domains_schema.dump(domains)

@domains_bp.route("/<int:domain_id>")
def get_one_domain(domain_id):
    stmt = db.select(Domain).filter_by(id=domain_id)
    domain = db.session.scalar(stmt)
    if domain:
        return domain_schema.dump(domain)
    else:
        return {"error": f"Domain with id {domain_id} not found"}, 404
    
@domains_bp.route("/", methods=["POST"])
@jwt_required()
def register_domain():
    body_data = request.get_json()
    domain = Domain(
        domain_name=body_data.get("domain_name"),
        registered_period=body_data.get("registered_period"),
        user_id=get_jwt_identity()
    )
    db.session.add(domain)
    db.session.commit()
    return domain_schema.dump(domain)

@domains_bp.route("/<int:domain_id>", methods=["DELETE"])
@jwt_required()
def unregister_domain(domain_id):
    stmt = db.select(Domain).filter_by(id=domain_id)
    domain = db.session.scalar(stmt)
    if domain:
        db.session.delete(domain)
        db.session.commit()
        return {"message": f"Domain id '{domain_id}' unregistered successfully"}
    else:
        return {"error": f"Domain with id '{domain_id}' not found"}, 404

@domains_bp.route("/<int:domain_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_domain(domain_id):
    body_data = request.get_json()
    stmt = db.select(Domain).filter_by(id=domain_id)
    domain = db.session.scalar(stmt)
    if domain:
        domain.domain_name = body_data.get("domain_name") or domain.domain_name
        domain.registered_period = body_data.get("registered_period") or domain.registered_period
        domain.expiry_date = domain.registered_date + timedelta(days=domain.registered_period * 365) 

        db.session.commit()
        return domain_schema.dump(domain)
    else:
        return {"error": f"Domain with id '{domain_id}' not found"}, 404

@domains_bp.route("/<int:domain_id>/services", methods=["POST"])
@jwt_required()
def add_service_to_domain(domain_id):
    body_data = request.get_json()
    service_id = body_data.get("service_id")

    domain_stmt = db.select(Domain).filter_by(id=domain_id)
    service_stmt = db.select(Service).filter_by(id=service_id)

    domain = db.session.scalar(domain_stmt)
    service = db.session.scalar(service_stmt)

    if domain and service:
        domain_service = Domain_Service(
            domain_id=domain.id, 
            service_id=service.id, 
            domain_price=domain.domain_price, 
            service_price=service.service_price
            )
        db.session.add(domain_service)
        db.session.commit()
        return domain_service_schema.dump(domain_service)
    else:
        return {"error": "Invalid domain or service ID"}, 404
