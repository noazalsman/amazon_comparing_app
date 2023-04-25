# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class SearchData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(255), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    amazon_com_price = db.Column(db.Float, nullable=False)
    amazon_co_uk_price = db.Column(db.Float, nullable=False)
    amazon_de_price = db.Column(db.Float, nullable=False)
    amazon_ca_price = db.Column(db.Float, nullable=False)
