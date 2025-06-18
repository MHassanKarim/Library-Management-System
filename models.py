from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy(session_options={"autoflush": False})

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    publisher = db.Column(db.String(100))
    pages = db.Column(db.Integer)
    copies = db.Column(db.Integer, nullable=False)
    transactions = db.relationship('Transaction', backref='book', lazy=True)
    
    def __repr__(self):
        return f'<Book {self.title}>'

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    transactions = db.relationship('Transaction', backref='member', lazy=True)
    
    def __repr__(self):
        return f'<Member {self.name}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    issue_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Transaction {self.id}>'