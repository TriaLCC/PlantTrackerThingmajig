from . import db

collection_plants = db.Table(
    'collection_plants',
    db.Column('collection_id', db.Integer, db.ForeignKey('collection.id'), primary_key=True),
    db.Column('plant_id', db.Integer, db.ForeignKey('plant.id'), primary_key=True),
)

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    watering_days = db.Column(db.String(128))
    notes = db.Column(db.Text)

    @property
    def watering_days_list(self):
        if self.watering_days:
            return [d for d in [s.strip() for s in self.watering_days.split(',')] if d]
        return []


class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    plants = db.relationship('Plant', secondary=collection_plants, backref='collections')