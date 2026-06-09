from flask import Blueprint, request, render_template, redirect, url_for
import datetime
from . import db
from .models import Plant, Collection

bp = Blueprint('api', __name__)

# Allowed day names for watering schedule
ALLOWED_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Validate that watering_days is a list of days from ALLOWED_DAYS
def validate_days(days):
    if not isinstance(days, (list, tuple)):
        return False
    return all(d in ALLOWED_DAYS for d in days)

# Landing Page showing summary and today's watering stuffs
@bp.route("/")
def homepage():
    plants = Plant.query.all()
    collections = Collection.query.all()
    # compute today's name and how many plants need watering today
    today_name = datetime.date.today().strftime('%A')
    today_count = 0
    for p in plants:
        wd_list = getattr(p, 'watering_days_list', [])
        if today_name in wd_list:
            today_count += 1

    return render_template('index.html', plants=plants, collections=collections,
                           plants_count=len(plants), collections_count=len(collections),
                           today_name=today_name, today_count=today_count)


# Begin API routes for API CRUD ops for Plants

# Plant UI page
@bp.route('/plants/ui')
def plants_page():
    # collection filter - in case I want to play favorites with only some of my plants and let the rest die
    col_id = request.args.get('collection_id', type=int)
    collections = Collection.query.all()
    if col_id:
        col = Collection.query.get_or_404(col_id)
        plants = col.plants
    else:
        plants = Plant.query.all()
    return render_template('plants.html', plants=plants, collections=collections, selected_collection=col_id)

# CrEATE
@bp.route('/plants/new', methods=['GET', 'POST'])
def new_plant_page():
    if request.method == 'POST':
        name = request.form.get('name')
        watering_days = request.form.getlist('watering_days')
        notes = request.form.get('notes')
        if not name or not watering_days:
            return "name and at least one watering day required", 400
        # store as comma-separated string - really this makes more sense as a dimension table but whatevs...
        plant = Plant(name=name, watering_days=','.join(watering_days), notes=notes)
        db.session.add(plant)
        db.session.commit()
        return redirect(url_for('api.plants_page'))
    return render_template('plant_form.html', plant=None, days=ALLOWED_DAYS)

# UPDATE
@bp.route('/plants/<int:plant_id>/edit', methods=['GET', 'POST'])
def edit_plant_page(plant_id):
    plant = Plant.query.get_or_404(plant_id)
    if request.method == 'POST':
        plant.name = request.form.get('name') or plant.name
        watering_days = request.form.getlist('watering_days')
        if watering_days:
            plant.watering_days = ','.join(watering_days)
        plant.notes = request.form.get('notes')
        db.session.commit()
        return redirect(url_for('api.plants_page'))
    return render_template('plant_form.html', plant=plant, days=ALLOWED_DAYS)

#DELETE
@bp.route('/plants/<int:plant_id>/delete', methods=['POST'])
def delete_plant_ui(plant_id):
    plant = Plant.query.get_or_404(plant_id)
    db.session.delete(plant)
    db.session.commit()
    return redirect(url_for('api.plants_page'))
# End API routes for API CRUD ops for Plants

# Begin API routes for API CRUD ops for Collecions
@bp.route('/plants/<int:plant_id>/add_to_collection', methods=['POST'])
def add_plant_to_collection_ui(plant_id):
    plant = Plant.query.get_or_404(plant_id)
    col_id = request.form.get('collection_id', type=int)
    if not col_id:
        return redirect(url_for('api.plants_page'))
    col = Collection.query.get_or_404(col_id)
    if plant not in col.plants:
        col.plants.append(plant)
        db.session.commit()
    return redirect(url_for('api.plants_page', collection_id=col_id))

# READ, CREATE, and
@bp.route('/collections/ui', methods=['GET', 'POST'])
def collections_page():
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            return "name required", 400
        col = Collection(name=name)
        db.session.add(col)
        db.session.commit()
        return redirect(url_for('api.collections_page'))
    cols = Collection.query.all()
    return render_template('collections.html', collections=cols)


@bp.route('/collections/<int:col_id>/delete', methods=['POST'])
def delete_collection_ui(col_id):
    col = Collection.query.get_or_404(col_id)
    db.session.delete(col)
    db.session.commit()
    return redirect(url_for('api.collections_page'))

# Show schedule
@bp.route('/schedule/ui')
def schedule_page():
    # Optional collection filter
    col_id = request.args.get('collection_id', type=int)
    collections = Collection.query.all()
    if col_id:
        col = Collection.query.get_or_404(col_id)
        plants = col.plants
    else:
        plants = Plant.query.all()

    # Loop over all the allowed days, see which plants get watered and add them to an array for that day
    schedule = {day: [] for day in ALLOWED_DAYS}
    for plant in plants:
        for d in getattr(plant, 'watering_days_list', []):
            if d in schedule:
                schedule[d].append(plant)

    return render_template('schedule.html', schedule=schedule, collections=collections, selected_collection=col_id)
