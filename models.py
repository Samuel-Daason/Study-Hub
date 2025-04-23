from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# The Subject model
class Subject(db.Model):
    __tablename__ = 'subject'  # Explicitly set table name for clarity

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # Relationship with Paper: one subject can have many papers
    papers = db.relationship(
        'Paper',
        backref='subject',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def __repr__(self):
        return f'<Subject {self.name}>'

# The Paper model
class Paper(db.Model):
    __tablename__ = 'paper'  # Explicitly set table name for clarity

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(200), nullable=False)  # Path to the uploaded paper file
    subject_id = db.Column(
        db.Integer,
        db.ForeignKey('subject.id', ondelete='CASCADE'),  # Allow deletion of papers when subject is deleted
        nullable=False
    )

    def __repr__(self):
        return f'<Paper {self.name}>'
