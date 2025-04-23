from flask import Flask, render_template, send_from_directory, request, redirect
from models import db, Subject
from catalogue_routes import catalogue_routes, view_papers

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalogue.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Cascade deletion
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


db.init_app(app)

# Secret Key for runtime and cookies 

app.config['SECRET_KEY'] = '1423'


# Home page
@app.route('/', methods=['GET', 'POST'])
def index():
    subjects = Subject.query.all()

    if request.method == 'POST':
        subject_name = request.form.get('subject_name')
        subject_description = request.form.get('subject_description')
        subject_id = request.form.get('subject_id')

        if subject_id:  # Update existing subject
            subject = Subject.query.get(int(subject_id))
            if subject:
                subject.name = subject_name
                subject.description = subject_description
        else:  # Create new subject
            new_subject = Subject(name=subject_name, description=subject_description)
            db.session.add(new_subject)

        db.session.commit()
        return redirect('/')

    return render_template('index.html', subjects=subjects)


# View all papers in a subject 
@app.route('/<subject_name>')
def subject_page(subject_name):
    return view_papers(subject_name)


# Serve custom JS
@app.route('/scripts/<path:path>')
def send_js(path):
    return send_from_directory('scripts/js', path)


# Register paper-related routes
app.register_blueprint(catalogue_routes, url_prefix='/catalog')


# Create the database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
