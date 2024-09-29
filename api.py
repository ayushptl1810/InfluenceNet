from functools import wraps
from flask_restful import Resource, Api, reqparse
from flask import request
from app import app
from models import db, User, Campaign
from datetime import datetime

api = Api(app)

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        auth_token = request.headers.get('X-AUTH-TOKEN')

        if auth_token == app.config['ADMIN_AUTH_TOKEN']:
            return func(*args, **kwargs)
        else:
            return {"message": "Unauthoroised Access"}, 401

    return inner

class CampaignResource(Resource):
    @auth_required
    def get(self, campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)

        return { 
            'id': campaign.id,
            'campaign_name' : campaign.campaign_name,
            'description': campaign.description,
            'goals': campaign.goals,
            'start_date': campaign.start_date.strftime('%Y-%m-%d %H:%M:%S'),
            'end_date': campaign.end_date.strftime('%Y-%m-%d %H:%M:%S'),
            'budget': campaign.budget,
            'niche': campaign.niche,
            'visibility': campaign.visibility,
            'sponsor_id': campaign.sponsor_id
        }
    
    @auth_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('sponsor_id', type = int, required = True)
        parser.add_argument('campaign_name', type = str, required = True)
        parser.add_argument('description', type = str, required = True)
        parser.add_argument('goals', type = str, required = True)
        parser.add_argument('start_date', type = str, required = True)
        parser.add_argument('end_date', type = str, required = True)
        parser.add_argument('budget', type = int, required = True)
        parser.add_argument('niche', type = str, required = True)
        parser.add_argument('visibility', type = bool, required = True)
        
        args = parser.parse_args()
        start_date = datetime.strptime(args['start_date'], '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(args['end_date'], '%Y-%m-%d %H:%M:%S')

        new_campaign = Campaign(campaign_name = args['campaign_name'],
                                description = args['description'], 
                                goals = args['goals'], 
                                start_date = start_date, 
                                end_date = end_date, 
                                budget = args['budget'],
                                visibility = args['visibility'],
                                sponsor_id = args['sponsor_id'], 
                                niche = args['niche'])


        db.session.add(new_campaign)
        db.session.commit()

        return { 'id' : new_campaign.id }, 200
    
    @auth_required
    def delete(self, campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        db.session.delete(campaign)
        db.session.commit()
        
        return {"message": "Campaign Deleted"}, 200
    
    @auth_required
    def put(self, campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        parser = reqparse.RequestParser()

        auth_token = request.headers.get('X-AUTH-TOKEN')
        if auth_token != app.config['ADMIN_AUTH_TOKEN'] :
            return {"message": "Unauthoroised Access"}, 401

        parser.add_argument('sponsor_id', type = int, required = True)
        parser.add_argument('campaign_name', type = str, required = True)
        parser.add_argument('description', type = str, required = True)
        parser.add_argument('goals', type = str, required = True)
        parser.add_argument('start_date', type = str, required = True)
        parser.add_argument('end_date', type = str, required = True)
        parser.add_argument('budget', type = int, required = True)
        parser.add_argument('niche', type = str, required = True)
        parser.add_argument('visibility', type = bool, required = True)
        
        args = parser.parse_args()
        start_date = datetime.strptime(args['start_date'], '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(args['end_date'], '%Y-%m-%d %H:%M:%S')

        campaign.campaign_name = args['campaign_name']
        campaign.description = args['description']
        campaign.goals = args['goals']
        campaign.start_date = start_date
        campaign.end_date = end_date
        campaign.budget = args['budget']
        campaign.niche = args['niche']
        campaign.visibility = args['visibility']

        db.session.commit()

        return { 'id' : campaign.id }, 200

from sqlalchemy.exc import IntegrityError
@app.errorhandler(IntegrityError)
def handle_integrity_error(error):
    db.session.rollback()
    return {'message': 'A Constraint was violated'}, 400

api.add_resource(CampaignResource, '/api/campaign', '/api/campaign/<int:campaign_id>')

