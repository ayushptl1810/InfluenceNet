from flask import render_template, request, redirect, url_for, flash, session
from app import app
from models import db, User, Influencer, Sponsor, Campaign, Ad_Request, Flag, StatusEnum
from sqlalchemy import desc, func, and_
from sqlalchemy.orm import aliased
from functools import wraps
from utils import strtobool
from datetime import datetime, timezone
import os
from werkzeug.utils import secure_filename
from config import nicheList, categoryList
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Please fill out all fields')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('Username does not exist')
        return redirect(url_for('login'))
    
    if user.password !=  password:
        flash('Incorrect password')
        return redirect(url_for('login'))
    
    session['user_id'] = user.id
    session['user_role'] = user.role
        
    return redirect(url_for('home'))

@app.route('/register_sponsor')
def register_sponsor(): 
    return render_template('register_sponsor.html')

@app.route('/register_sponsor', methods=['POST'])
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    name = request.form.get('name')
    company = request.form.get('company')
    industry = request.form.get('industry')
    if not username or not password or not confirm_password or not company or not industry:
        flash('Please fill out all fields')
        return redirect(url_for('register_sponsor'))
    
    if password != confirm_password:
        flash('Passwords do not match')
        return redirect(url_for('register_sponsor'))
    
    user = User.query.filter_by(username=username).first()

    if user:
        flash('Username already exists')
        return redirect(url_for('register_sponsor'))
    
    flash('Sponsor created successfully')

    new_user = Sponsor(username=username, password=password, name=name, company=company, industry=industry, role='sponsor')
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))

@app.route('/register_influencer')
def register_influencer(): 
    return render_template('register_influencer.html', niche=nicheList, category=categoryList)

@app.route('/register_influencer', methods=['POST'])
def register_influencer_post():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    name = request.form.get('name')
    category = request.form.get('category')
    niche = request.form.get('niche')
    reach = request.form.get('reach')
    if not username or not password or not confirm_password or not name or not category or not niche or not reach:
        flash('Please fill out all fields')
        return redirect(url_for('register_influencer'))
    
    if password != confirm_password:
        flash('Passwords do not match')
        return redirect(url_for('register_influencer'))
    
    user = User.query.filter_by(username=username).first()

    if user:
        flash('Username already exists')
        return redirect(url_for('register_influencer'))
    
    flash('Influencer created successfully')

    new_user = Influencer(username=username, password=password, name=name, category=category, niche=niche, reach=reach, role='influencer')
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash('Please login to continue')
            return redirect(url_for('login'))
    return inner

def admin_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session and session.get('user_role') == 'admin':
            return func(*args, **kwargs)
        else:
            flash('Admin access required')
            return redirect(url_for('login'))
    return inner

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS'] 

@app.route('/upload_profile_pic', methods=['POST'])
@auth_required
def upload_profile_pic():
    if 'profile_pic' not in request.files:
        flash('No file part')
        return redirect(url_for('profile_influencer'))
    
    file = request.files['profile_pic']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('profile_influencer'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        user_id = session['user_id']

        new_filename = f"user_{user_id}.{filename.rsplit('.', 1)[1].lower()}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))

        user = User.query.get(user_id)
        user.profile_pic = new_filename
        db.session.commit()
        
        flash('Profile picture updated successfully')
        return redirect(url_for('profile_influencer'))
    
    flash('Invalid file format')
    return redirect(url_for('home'))

@app.route('/')
@auth_required
def home():
    user_role = session['user_role']
    
    if user_role == 'sponsor':
        return redirect(url_for('home_sponsor'))
    elif user_role == 'influencer':
        return redirect(url_for('home_influencer'))
    elif user_role == 'admin':
        return redirect(url_for('home_admin'))
    else:
        flash('Unknown user role')
        return redirect(url_for('login'))

@app.route('/home_sponsor')
@auth_required
def home_sponsor():
    user_role = session['user_role']
    user_id = session['user_id']
    if user_role != 'sponsor':
        return redirect(url_for('login'))
    
    current_time = datetime.now(timezone.utc)
    user = User.query.get(user_id)

    campaigns = Campaign.query.filter(
                        Campaign.sponsor_id == user_id,
                        Campaign.end_date >= current_time
                        ).all()
    
    ad_requests = (db.session.query(Ad_Request)
                        .join(Campaign)
                        .filter(Campaign.sponsor_id == user_id)
                        .filter(Ad_Request.status == StatusEnum.pending)
                        .filter(Ad_Request.requested_by == 'influencer')
                        .all())              

    flagged_user_list = Flag.query.filter_by(flagged_by_id = user_id).all()  
    flagged_user_ids = [flag.user_id for flag in flagged_user_list]

    return render_template('home_sponsor.html', ad_requests=ad_requests, campaigns=campaigns, user=user, niche=nicheList, flagged_user_ids=flagged_user_ids)

@app.route('/home_influencer')
@auth_required
def home_influencer():
    user_role = session['user_role']
    user_id = session['user_id']
    if user_role != 'influencer':
        return redirect(url_for('login'))   

    user = User.query.get(user_id)
    campaigns = (db.session.query(Campaign)
                    .join(Ad_Request)
                    .filter(Ad_Request.influencer_id == user_id)
                    .filter(Ad_Request.status == StatusEnum.accepted)
                    .all())
        
    flagged_user_list = Flag.query.filter_by(flagged_by_id = user_id).all()
    flagged_user_ids = [flag.user_id for flag in flagged_user_list]

    ad_requests = Ad_Request.query.filter_by(status = StatusEnum.pending, requested_by = 'sponsor', influencer_id = user_id).all() 
    ad_requests_influencer = Ad_Request.query.filter_by(status = StatusEnum.pending, requested_by = 'influencer', influencer_id = user_id).all() 

    return render_template('home_influencer.html', campaigns=campaigns, ad_requests=ad_requests, user=user, flagged_user_ids=flagged_user_ids, ad_requests_influencer=ad_requests_influencer)

@app.route('/home_admin')
@admin_required
def home_admin():
    user_count = User.query.count()
    sponsor_count = Sponsor.query.count()
    influencer_count = Influencer.query.count()
    active_campaign_count = Campaign.query.filter(Campaign.end_date >= datetime.now(timezone.utc)).count()
    

    data = db.session.query(
        func.date(Ad_Request.completed_date), 
        func.sum(Ad_Request.payment_amount).label('earnings')).filter(and_(Ad_Request.completed_date != None)).group_by(func.date(Ad_Request.completed_date)).order_by(Ad_Request.completed_date).all()

    if data:
        dates = [d[0] for d in data if d[0]]
        earnings = [d[1] for d in data if d[1]]

        plt.figure(figsize=(16, 8))
        plt.plot(dates, earnings, color='#c7ae6a') 
        plt.xlabel('Date', fontsize=14, color='#c7ae6a')
        plt.ylabel('Earnings', fontsize=14, color='#c7ae6a')
        plt.title('Daily Earnings for July 2024', fontsize=16, color='#c7ae6a')
        plt.grid(True)
        plt.xticks(rotation=30)

        plt.gcf().set_facecolor('#171717')  
        plt.gca().set_facecolor('#333333')
        plt.xticks(color='#c7ae6a') 
        plt.yticks(color='#c7ae6a')

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
    
        graph_base64 = base64.b64encode(image_png).decode('utf-8')
    
        return render_template('home_admin.html', user_count=user_count, sponsor_count=sponsor_count, influencer_count=influencer_count, active_campaign_count=active_campaign_count, graph_base64=graph_base64)
    
    return render_template('home_admin.html', user_count=user_count, sponsor_count=sponsor_count, influencer_count=influencer_count, active_campaign_count=active_campaign_count)

@app.route('/logout')
@auth_required
def logout():
    session.pop('user_id')
    return redirect(url_for('login'))

@app.route('/create_campaign', methods=['POST'])
@auth_required
def create_campaign_post():
    campaign_name = request.form.get('campaign_name')
    description = request.form.get('description')
    goals = request.form.get('goals')
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    budget = request.form.get('budget')
    niche = request.form.get('niche')
    visibility = bool(strtobool(request.form.get('visibility', 'False')))
    sponsor_id = session['user_id']

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)

    current_time = datetime.now(timezone.utc)

    if not campaign_name or not description or not start_date or not end_date or not budget or not goals or not niche:
        flash('Please fill out all fields')
        return redirect(url_for('home'))
    
    if current_time > end_date:
        flash('The campaign cannot be created because the end date has already passed.')
        return redirect(url_for('home'))

    if start_date >= end_date:
        flash('The campaign start date must be earlier than the end date.')
        return redirect(url_for('home'))

    campaign = Campaign.query.filter_by(campaign_name=campaign_name).first()
    if campaign:
        flash('Campaign name already exists')
        return redirect(url_for('home'))
    
    flash('Campaign created successfully')

    new_campaign = Campaign(campaign_name=campaign_name, description=description, goals=goals, start_date=start_date, end_date=end_date, budget=budget, visibility=visibility, sponsor_id=sponsor_id, niche=niche)
    db.session.add(new_campaign)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/view_campaign')
@auth_required
def view_campaign():
    campaign_id = request.args.get('campaign_id')
    campaign = Campaign.query.filter_by(id=campaign_id).first()

    user = User.query.filter_by(id = campaign.sponsor_id).first()

    accepted_ad_requests = Ad_Request.query.filter_by(campaign_id = campaign_id, status = StatusEnum.accepted).all()
    ad_request_status = Ad_Request.query.filter(Ad_Request.campaign_id == campaign_id, Ad_Request.status.in_([StatusEnum.pending, StatusEnum.rejected, StatusEnum.cancelled])).all()
    ad_request_completed = Ad_Request.query.filter_by(campaign_id = campaign_id, status = StatusEnum.completed).all()

    return render_template('view_campaign.html', campaign=campaign, accepted_ad_requests=accepted_ad_requests, ad_request_status=ad_request_status, ad_request_completed=ad_request_completed, niche=nicheList, user=user)

@app.route('/edit_campaign', methods = ['POST'])
@auth_required
def edit_campaign_post():
    campaign_id = request.form.get('id')
    campaign_name = request.form.get('campaign_name')
    description = request.form.get('description')
    goals = request.form.get('goals')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    budget = request.form.get('budget')
    niche = request.form.get('niche')
    visibility = bool(strtobool(request.form.get('visibility', 'False')))

    current_time = datetime.now(timezone.utc)

    start_date = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)

    campaign = Campaign.query.get(campaign_id)

    if not campaign:
        flash('Campaign ID not found')
        return redirect(url_for('home'))   
    
    if not campaign_name or not description or not start_date or not end_date or not budget or not goals or not niche:
        flash('Please fill out all fields')
        return redirect(url_for('home'))
    
    if current_time > end_date:
        flash('The end date cannot be modified as it has already passed')
        return redirect(url_for('home'))
    
    campaign.campaign_name = campaign_name
    campaign.description = description
    campaign.goals = goals
    campaign.start_date = start_date
    campaign.end_date = end_date
    campaign.budget = budget
    campaign.niche = niche
    campaign.visibility = visibility

    db.session.commit()
    flash('Campaign edited successfully')

    return redirect(url_for('view_campaign', campaign_id=campaign_id))

@app.route('/delete_campaign')
@auth_required
def delete_campaign():
    campaign_id = request.args.get('campaign_id')
    campaign = Campaign.query.get(campaign_id)

    ad_request = Ad_Request.query.filter_by(campaign_id = campaign_id).first()
    if not ad_request:
        db.session.delete(campaign)
        db.session.commit()
        flash('Campaign deleted successfully')
    
    else:
        flash('Unable to delete the campaign due to associated ad requests')

    return redirect(url_for('home'))

@app.route('/create_ad_request', methods = ['POST'])
@auth_required
def create_ad_request_post():
    requested_by = session['user_role']
    campaign_id = request.form.get('campaign_id')

    if session['user_role'] == 'influencer':
        influencer_id = session['user_id']
    else:
        influencer_id = request.form.get('influencer_id')

    message = request.form.get('message')
    requirements = request.form.get('requirements')
    payment_amount = request.form.get('payment_amount')

    if not message or not requirements or not payment_amount:
        flash('Please fill out all the fields')

    ad_requests = Ad_Request.query.filter(
        Ad_Request.campaign_id == campaign_id,
        Ad_Request.influencer_id == influencer_id,
        Ad_Request.status.in_([StatusEnum.pending, StatusEnum.accepted])
    ).first()
    if ad_requests:
        flash('Only one active ad request can be sent at a time')
        return redirect(url_for('home'))

    new_ad_request = Ad_Request(requested_by=requested_by, campaign_id=campaign_id, influencer_id=influencer_id, message=message, requirements=requirements, payment_amount=payment_amount)
    db.session.add(new_ad_request)
    db.session.commit()
    flash('Ad Request sent successfully')

    return redirect(url_for('home'))

@app.route('/view_ad_request')
@auth_required
def view_ad_request():
    user_role = session['user_role']
    ad_request_id = request.args.get('id')
    ad_request = Ad_Request.query.get(ad_request_id)

    if not ad_request:
        flash('Ad request not found')
        return redirect(url_for('home'))
    
    ad_requests_history = Ad_Request.query.filter_by(campaign_id=ad_request.campaign_id, influencer_id=ad_request.influencer_id, status = StatusEnum.accepted).order_by(desc(Ad_Request.created_at)).all()

    return render_template('view_ad_request.html', influencer = ad_request.influencer, ad_request = ad_request, campaign = ad_request.campaign, user_role = user_role, ad_requests_history = ad_requests_history)

@app.route('/update_ad_request', methods = ['POST'])
@auth_required
def update_ad_request():
    ad_request_id = request.form.get('ad_request_id')
    ad_request = Ad_Request.query.get(ad_request_id)
    if ad_request.status == StatusEnum.pending:
        message = request.form.get('message')
        requirements = request.form.get('requirements')
        payment_amount = request.form.get('payment_amount')

        ad_request.message = message
        ad_request.requirements = requirements
        ad_request.payment_amount = payment_amount

        db.session.commit()
        flash("Ad Requested updated successfully")

    else:
        flash("Ad request has been rejected, send a new request")

    return redirect(url_for('home'))

@app.route('/delete_ad_request')
@auth_required
def delete_ad_request():
    ad_request_id = request.args.get('ad_request_id')
    ad_request = Ad_Request.query.get(ad_request_id)

    ad_request.status = StatusEnum.cancelled
    db.session.commit()
    flash("Ad request cancelled successfully")

    return redirect(url_for('home'))

@app.route('/search_influencer')
@auth_required
def search_influencer():
    reach = 10000
    return render_template('search_influencer.html', categoryList=categoryList, reach=reach)

@app.route('/search_influencer', methods = ['POST'])
@auth_required
def search_influencer_post():
    query = Influencer.query
    filters = []
    id = session['user_id']
    campaigns = db.session.query(Campaign).filter(
        Campaign.sponsor_id == id,
        Campaign.start_date < datetime.now(timezone.utc),
        Campaign.end_date > datetime.now(timezone.utc)
    ).all()

    username = request.form.get('username')
    category = request.form.get('category')
    reach = request.form.get('reach')

    if username:
        filters.append(Influencer.username.like(f"%{username}%"))
    if category:
        filters.append(Influencer.category == category)
    if reach:
        filters.append(Influencer.reach >= int(reach))

    if filters:
        query = query.filter(*filters)

    results = query.all()

    return render_template('search_influencer.html', results = results, campaigns=campaigns, reach=reach, categoryList=categoryList)

@app.route('/search_campaign')
@auth_required
def search_campaign():
    budget = 10000
    return render_template('search_campaign.html', nicheList=nicheList, budget = budget)

@app.route('/search_campaign', methods = ['POST'])
@auth_required
def search_campaign_post():
    query = Campaign.query.filter_by(visibility = True)
    filters = []

    niche = request.form.get('niche')
    budget = request.form.get('budget')

    if niche:
        filters.append(Campaign.niche == niche)
    if budget:
        filters.append(Campaign.budget <= int(budget))
    
    current_date = datetime.now()
    filters.append(Campaign.start_date <= current_date)
    filters.append(Campaign.end_date >= current_date)

    if filters:
        query = query.filter(*filters)

    campaigns = query.all()

    return render_template('search_campaign.html', campaigns=campaigns, budget=budget, nicheList=nicheList)

@app.route('/reject')
@auth_required
def reject():
    id  = request.args.get('id')
    ad_request = Ad_Request.query.get(id)
    
    if not ad_request:
        flash('Ad request not found')
        return redirect(url_for('home'))
    
    ad_request.status = StatusEnum.rejected
    db.session.commit()

    flash('Ad Request rejected successfully')
    return redirect(url_for('home'))

@app.route('/accept')
@auth_required
def accept():
    id  = request.args.get('id')
    ad_request = Ad_Request.query.get(id)
    
    if not ad_request:
        flash('Ad request not found')
        return redirect(url_for('home'))
    
    ad_request.status = StatusEnum.accepted
    db.session.commit()

    flash('Ad Request accepted successfully')
    return redirect(url_for('home'))
    
@app.route('/renegotiate', methods = ['POST'])
@auth_required
def renegotiate_post():
    id = request.form.get('id')
    ad_request = Ad_Request.query.get(id)

    if not ad_request:
        flash('Ad request not found')
        return redirect(url_for('home'))

    requested_by = session['user_role']
    message = request.form.get('message')
    requirements = request.form.get('requirements')
    payment_amount = request.form.get('payment_amount')
    ad_request.status = StatusEnum.responded

    new_ad_request = Ad_Request(requested_by=requested_by, campaign_id=ad_request.campaign_id, influencer_id=ad_request.influencer_id, message=message, requirements=requirements, payment_amount=payment_amount)
    db.session.add(new_ad_request)
    db.session.commit()

    return redirect(url_for('home'))
    
@app.route('/profile_influencer')
@auth_required
def profile_influencer():
    user_id = session['user_id']
    user = User.query.get(user_id)
    influencer = Influencer.query.get(user_id)
    
    data = db.session.query(
        func.date(Ad_Request.completed_date), 
        func.sum(Ad_Request.payment_amount).label('earnings')
    ).filter(Ad_Request.influencer_id == user_id, and_(Ad_Request.completed_date != None)).group_by(func.date(Ad_Request.completed_date)).order_by(Ad_Request.completed_date).all()

    dates = [d[0] for d in data]
    earnings = [d[1] for d in data]

    plt.figure(figsize=(16, 8))
    plt.plot(dates, earnings, color='#c7ae6a') 
    plt.xlabel('Date', fontsize=14, color='#c7ae6a')
    plt.ylabel('Earnings', fontsize=14, color='#c7ae6a')
    plt.title('Daily Earnings for Influencer', fontsize=16, color='#c7ae6a')
    plt.grid(True)
    plt.xticks(rotation=30)

    plt.gcf().set_facecolor('#171717')  
    plt.gca().set_facecolor('#333333')
    plt.xticks(color='#c7ae6a') 
    plt.yticks(color='#c7ae6a')

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    graph_base64 = base64.b64encode(image_png).decode('utf-8')
    return render_template('profile_influencer.html', influencer=influencer, user=user, niche=nicheList, category=categoryList, graph_base64=graph_base64)
    
@app.route('/profile_influencer', methods = ['POST'])
@auth_required
def profile_influencer_post():
    id = request.form.get('id')
    username = request.form.get('username')
    bio = request.form.get('bio', '')
    niche = request.form.get('niche')
    category = request.form.get('category')
    reach = request.form.get('reach')

    influencer = Influencer.query.get(id)

    if not influencer:
        flash('Influencer not found')
        return redirect(url_for('home'))
    
    if not username or not niche or not category or not reach:
        flash('Fill required fields')
        return redirect(url_for('profile_influencer'))
    
    influencer.username = username
    influencer.bio = bio
    influencer.niche = niche
    influencer.category = category
    influencer.reach = reach

    db.session.commit()
    return redirect(url_for('profile_influencer'))

@app.route('/completed')
@auth_required
def completed():
    id = request.args.get('id')
    ad_request = Ad_Request.query.get(id)

    if not ad_request:
        flash('Ad Request does not exist')
        return redirect(url_for('home'))
    
    ad_request.status = StatusEnum.completed
    ad_request.completed_date = datetime.now()

    influencer = ad_request.influencer
    if influencer:
        if influencer.earnings is None:
            influencer.earnings = 0
        influencer.earnings += ad_request.payment_amount

    db.session.commit()
    flash('Ad Request marked completed successfully')
     
    return redirect(url_for('home'))

@app.route('/completed_campaigns')
@auth_required
def completed_campaigns():
    id = session['user_id']

    if session['user_role'] == 'sponsor':
        completed_campaigns = db.session.query(Campaign).filter(
            Campaign.sponsor_id == id,
            Campaign.end_date < datetime.now(timezone.utc)
        ).all()
        return render_template('completed_campaigns.html', completed_campaigns = completed_campaigns)

    elif session['user_role'] == 'influencer':
        completed_ad_requests = db.session.query(Ad_Request).filter(
            Ad_Request.influencer_id == id,
            Ad_Request.status == StatusEnum.completed
        ).all()
        return render_template('completed_campaigns.html', completed_ad_requests = completed_ad_requests)

@app.route('/flagged', methods = ['POST'])
@auth_required
def flagged():

    if session['user_role'] == 'influencer':
        user_id = request.form.get('sponsor_id')
        flagged_by_id = session['user_id']

    elif session['user_role'] == 'sponsor':
        user_id = request.form.get('influencer_id')
        flagged_by_id = session['user_id']

    reason = request.form.get('reason')

    if not reason:
        flash('Please give a valid reason')
        return redirect(url_for('home'))
    
    new_flag = Flag(user_id=user_id, flagged_by_id=flagged_by_id, flag_reason=reason)
    db.session.add(new_flag)
    db.session.commit()
    flash('User flagged successfully')

    return redirect(url_for('home'))

@app.route('/flagged_user')
@admin_required
def flagged_user():
    flagged_user_alias = aliased(User)
    flagged_by_user_alias = aliased(User)

    flagged_users_query = db.session.query(
        flagged_user_alias.id.label('flagged_user_id'),
        flagged_user_alias.username.label('flagged_username'),
        Flag.flag_reason,
        flagged_by_user_alias.username.label('flagged_by_username'),
        Flag.flagged_at
    ).join(
        Flag, flagged_user_alias.id == Flag.user_id
    ).join(
        flagged_by_user_alias, flagged_by_user_alias.id == Flag.flagged_by_id
    ).all()

    flagged_users = []
    for row in flagged_users_query:
        flagged_user_id = row.flagged_user_id
        flagged_username = row.flagged_username
        flag_reason = row.flag_reason
        flagged_by_username = row.flagged_by_username
        flagged_at = row.flagged_at.strftime('%Y-%m-%d %H:%M:%S %Z')
        
        flagged_users.append({
            'flagged_user_id': flagged_user_id,
            'flagged_username': flagged_username,
            'flag_reason': flag_reason,
            'flagged_by_username': flagged_by_username,
            'flagged_at': flagged_at
        })
        
    return render_template('flagged_user.html', flagged_users = flagged_users)

@app.route('/unflag')
@admin_required
def unflag():
    user_id = request.args.get('id')
    flagged_user = Flag.query.filter_by(user_id=user_id).all()

    if not flagged_user:
            flash('Flagged user not found')
            return redirect(url_for('flagged_user'))
    
    for user in flagged_user:
        db.session.delete(user)
    db.session.commit()
    flash('Removed flag successfully')

    return redirect(url_for('flagged_user'))

@app.route('/delete_user')
@admin_required
def delete_user():
    user_id = request.args.get('id')
    user = User.query.get(user_id)

    if not user:
        flash('User not found')
        return redirect(url_for('flagged_user'))

    if user.role == 'sponsor':
            campaigns = Campaign.query.filter_by(sponsor_id=user_id).all()
            for campaign in campaigns:
                Ad_Request.query.filter_by(campaign_id=campaign.id).delete()
                db.session.delete(campaign)
        
    if user.role == 'influencer':
        Ad_Request.query.filter_by(influencer_id=user_id).delete()
        
    db.session.delete(user)
    db.session.commit()
    flash('Deleted User')

    return redirect(url_for('flagged_user'))