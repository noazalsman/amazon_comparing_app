# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class SearchData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(255), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    item_name = db.Column(db.String(255), nullable=True)
    amazon_com_price = db.Column(db.Float, nullable=True)
    amazon_co_uk_price = db.Column(db.Float, nullable=True)
    amazon_de_price = db.Column(db.Float, nullable=True)
    amazon_ca_price = db.Column(db.Float, nullable=True)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    daily_search_count = db.Column(db.Integer, nullable=False, default=0)
    last_search_date = db.Column(db.DateTime, nullable=True)
