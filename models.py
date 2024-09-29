from app import app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from sqlalchemy import Enum
import enum

db = SQLAlchemy(app)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(8))
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': role
    }

class Admin(User):
    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }

class Sponsor(User):
    __mapper_args__ = {
        'polymorphic_identity': 'sponsor',
    }
    company = db.Column(db.String(32))
    industry = db.Column(db.String(32))

class Influencer(User):
    __mapper_args__ = {
        'polymorphic_identity': 'influencer',
    }
    profile_pic = db.Column(db.String(32), default = 'default.jpeg')
    bio = db.Column(db.String[1024])
    category = db.Column(db.String(32))
    niche = db.Column(db.String(32))
    reach = db.Column(db.Double())
    earnings = db.Column(db.Double())
    ad_requests = db.relationship('Ad_Request', back_populates='influencer')


class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    campaign_name = db.Column(db.String(32), unique=True, nullable=False)
    description = db.Column(db.String(512), nullable=False)
    goals = db.Column(db.String(4096), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    budget = db.Column(db.Double(), nullable=False)
    visibility = db.Column(db.Boolean(), default = False)
    niche = db.Column(db.String(32), nullable=False)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    ad_requests = db.relationship('Ad_Request', back_populates='campaign')


class StatusEnum(enum.Enum):
    pending = 'Pending'
    responded = 'Responded'
    accepted = 'Accepted'
    rejected = 'Rejected'
    completed = 'Completed'
    cancelled = 'Cancelled'

class Ad_Request(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    requested_by = db.Column(db.String(16), nullable=False)
    campaign_id = db.Column(db.Integer(),  db.ForeignKey('campaign.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(4096))
    payment_amount = db.Column(db.Double(), nullable=False)
    status = db.Column(Enum(StatusEnum), default=StatusEnum.pending)
    requirements = db.Column(db.String(4096), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    completed_date = db.Column(db.DateTime)

    campaign = db.relationship('Campaign', back_populates='ad_requests')
    influencer = db.relationship('Influencer', back_populates='ad_requests')

class Flag(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    flag_reason = db.Column(db.String(512))
    flagged_by_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    flagged_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))


with app.app_context():
    db.create_all()
    
    admin = Admin.query.first()

    if not admin:
        admin = Admin(username = 'Admin1', password = '123', name = 'Kalpesh')
        db.session.add(admin)

        sponsor = Sponsor(username = 'Sponsor1', password = '123', name = 'Ayush', company = 'IT', industry = 'Tech')

        db.session.add(sponsor)
        db.session.commit()
        # sponsor = Sponsor.query.first()

        influencer = Influencer(username = 'Influencer1', password = '123', name = 'Kalpesh', category = 'Instagram', niche = 'Education', reach = 12345)
        campaign1 = Campaign(campaign_name = 'Campaign 1', description = 'Summer Wellness Challenge', goals = 'Increase Engagement', start_date = datetime(2024,5,13), end_date = datetime(2024,7,15), budget = 40000, niche = 'Tech', sponsor_id = sponsor.id)
        campaign2 = Campaign(campaign_name = 'Campaign 2', description = 'Back to School Prep', goals = 'Promote Brand Loyalty', start_date = datetime(2024,7,13), end_date = datetime(2024,8,13), budget = 40000, visibility = True, niche = 'Esports', sponsor_id = sponsor.id)

        db.session.add(influencer)
        db.session.add(campaign1)
        db.session.add(campaign2)
        db.session.commit()
        
        db.session.add(Ad_Request(requested_by = 'sponsor', campaign_id = campaign1.id, influencer_id = influencer.id, message = 'hi', requirements = 'hi', payment_amount = 20000, status= StatusEnum.completed, created_at = datetime(2024,6,1), completed_date = datetime(2024,7,14)))
        
        import random
        today = datetime.now()
        year = today.year
        month = today.month

        for i in range(1,31):
            amount = random.randint(1000, 10000)
            db.session.add(Ad_Request(requested_by = 'sponsor', campaign_id = campaign2.id, influencer_id = influencer.id, message = 'hi', requirements = 'hi', payment_amount = amount, status= StatusEnum.completed, created_at = datetime(2024,6,1), completed_date = datetime(year,month, i)))
        
        db.session.commit()

        
