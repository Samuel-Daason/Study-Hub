from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# User model
class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    reset_code = db.Column(db.String(6), nullable=True)
    reset_code_sent_at = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Subject model
class Subject(db.Model):
    __tablename__ = 'subject'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False
    )

    papers = db.relationship(
        'Paper',
        backref='subject',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def __repr__(self):
        return f'<Subject {self.name}>'


# Paper model
class Paper(db.Model):
    __tablename__ = 'paper'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(200), nullable=False)

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey('subject.id', ondelete='CASCADE'),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False
    )

    # Relationship to PaperNote with cascade delete
    notes = db.relationship(
        'PaperNote',
        back_populates='paper',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def __repr__(self):
        return f'<Paper {self.name}>'


# PaperNote model
class PaperNote(db.Model):
    __tablename__ = 'paper_note'

    id = db.Column(db.Integer, primary_key=True)
    time_spent = db.Column(db.Integer)
    score = db.Column(db.Integer)
    difficult_questions = db.Column(db.Text)
    difficulty_rating = db.Column(db.Integer)

    paper_id = db.Column(
        db.Integer,
        db.ForeignKey('paper.id', ondelete='CASCADE'),
        nullable=False
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False
    )

    # Relationships with back_populates to avoid conflicts
    paper = db.relationship('Paper', back_populates='notes')
    user = db.relationship('User', backref=db.backref('notes', lazy=True))

    def __repr__(self):
        return f'<PaperNote {self.id} for Paper {self.paper_id}>'
