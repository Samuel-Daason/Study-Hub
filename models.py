from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# User model
class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)  # Only email field now
    password_hash = db.Column(db.String(128), nullable=False)

    # Relationships
    subjects = db.relationship('Subject', backref='user', lazy=True, cascade='all, delete-orphan')
    papers = db.relationship('Paper', backref='user', lazy=True, cascade='all, delete-orphan')

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

    # Foreign key to User
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False
    )

    # Relationship with Paper
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

    # Foreign key to Subject
    subject_id = db.Column(
        db.Integer,
        db.ForeignKey('subject.id', ondelete='CASCADE'),
        nullable=False
    )

    # Foreign key to User
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False
    )

    def __repr__(self):
        return f'<Paper {self.name}>'
