from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Models (unchanged)
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    publisher = db.Column(db.String(100))
    pages = db.Column(db.Integer)
    copies = db.Column(db.Integer, nullable=False)
    transactions = db.relationship('Transaction', backref='book', lazy=True)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    transactions = db.relationship('Transaction', backref='member', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    issue_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime)

# Create tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    total_books = Book.query.count()
    total_members = Member.query.count()
    overdue_books = Transaction.query.filter(
        Transaction.return_date == None,
        Transaction.due_date < datetime.now()
    ).count()
    
    # Get recent transactions (5 most recent)
    recent_transactions = Transaction.query.order_by(Transaction.issue_date.desc()).limit(5).all()
    
    return render_template('index.html',
                         total_books=total_books,
                         total_members=total_members,
                         overdue_books=overdue_books,
                         transactions=recent_transactions)  # Pass transactions to template

# [Keep all your existing routes for books and members...]

# Transactions Routes - Improved
@app.route('/transactions')
def transactions():
    # Get all transactions with book and member details
    transactions = db.session.query(
        Transaction,
        Book.title,
        Member.name
    ).join(
        Book, Transaction.book_id == Book.id
    ).join(
        Member, Transaction.member_id == Member.id
    ).order_by(Transaction.issue_date.desc()).all()
    
    books = Book.query.filter(Book.copies > 0).all()  # Only show books with available copies
    members = Member.query.all()
    
    return render_template('transactions.html',
                         transactions=transactions,
                         books=books,
                         members=members)

@app.route('/issue_book', methods=['POST'])
def issue_book():
    try:
        book_id = request.form['book_id']
        member_id = request.form['member_id']
        due_date = datetime.now() + timedelta(days=14)  # 2 weeks due date
        
        book = Book.query.get_or_404(book_id)
        if book.copies <= 0:
            flash('No copies available for this book!', 'danger')
            return redirect(url_for('transactions'))
        
        # Check if member already has this book issued
        existing = Transaction.query.filter_by(
            book_id=book_id,
            member_id=member_id,
            return_date=None
        ).first()
        
        if existing:
            flash('This member already has this book checked out!', 'danger')
            return redirect(url_for('transactions'))
        
        book.copies -= 1
        
        new_transaction = Transaction(
            book_id=book_id,
            member_id=member_id,
            issue_date=datetime.now(),
            due_date=due_date
        )
        db.session.add(new_transaction)
        db.session.commit()
        
        flash('Book issued successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error issuing book: {str(e)}', 'danger')
    
    return redirect(url_for('transactions'))

@app.route('/return_book/<int:id>')
def return_book(id):
    try:
        transaction = Transaction.query.get_or_404(id)
        
        if transaction.return_date:
            flash('This book was already returned!', 'warning')
            return redirect(url_for('transactions'))
        
        transaction.return_date = datetime.now()
        book = Book.query.get_or_404(transaction.book_id)
        book.copies += 1
        
        db.session.commit()
        flash('Book returned successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error returning book: {str(e)}', 'danger')
    
    return redirect(url_for('transactions'))

if __name__ == '__main__':
    app.run(debug=True)