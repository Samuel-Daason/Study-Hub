from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models import db, Subject, Paper 
import os
from werkzeug.utils import secure_filename

# Define the blueprint
catalogue_routes = Blueprint('catalogue_routes', __name__)

# Define the absolute path to the static/papers folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'papers')

# Allowed file types (optional)
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'mp3', 'txt', 'doc', 'docx'}

# Check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Add paper route
@catalogue_routes.route('/add_paper/<subject_name>', methods=['GET', 'POST'])
def add_paper(subject_name):
    subject = Subject.query.filter_by(name=subject_name).first_or_404()

    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        description = request.form['description']
        file = request.files['file']

        # Validate that file is selected
        if not name or not description or not file:
            return "All fields (name, description, and file) are required.", 400

        # Check if the uploaded file type is allowed
        if file and allowed_file(file.filename):
            try:
                # Save the file to the upload folder
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)

                # Create and add the new paper to the database
                new_paper = Paper(
                    name=name,
                    description=description,
                    link=filename,
                    subject_id=subject.id
                )
                db.session.add(new_paper)
                db.session.commit()

                # Redirect to the page displaying the papers for that subject
                return redirect(url_for('catalogue_routes.view_papers', subject_name=subject_name))
            except Exception as e:
                # Handle potential errors during file saving or database operations
                return f"An error occurred while saving the paper: {str(e)}", 500
        else:
            return "Invalid file type. Please upload a valid file.", 400

    # Return the form for adding a new paper
    return render_template('add_paper.html', subject_name=subject_name)


# View paper routes
@catalogue_routes.route('/<subject_name>')
def view_papers(subject_name):
    # Query the subject by name, case-sensitive (or adjust as needed)
    subject = Subject.query.filter_by(name=subject_name).first_or_404()

    # Query papers related to the subject
    papers = Paper.query.filter_by(subject_id=subject.id).all()

    # Render the template with the subject name and the list of papers
    return render_template('view_papers.html', subject_name=subject_name, papers=papers)


# Delete paper route 
@catalogue_routes.route('/delete_paper/<subject_name>/<paper_id>', methods=['POST'])
def delete_paper(subject_name, paper_id):
    try:
        # Find the subject by its name
        subject = Subject.query.filter_by(name=subject_name).first()

        if not subject:
            # If subject is not found, handle it appropriately
            return f"Subject '{subject_name}' not found.", 404

        # Find the paper by its id within that subject
        paper = Paper.query.filter_by(id=paper_id, subject_id=subject.id).first()

        if not paper:
            # If the paper is not found, handle it appropriately
            return f"Paper with ID {paper_id} not found in subject '{subject_name}'.", 404

        # Delete the paper
        db.session.delete(paper)
        db.session.commit()

        # Redirect back to the subject's papers page after deletion
        return redirect(url_for('catalogue_routes.view_papers', subject_name=subject_name))

    except Exception as e:
        db.session.rollback()
        return f"Error deleting paper: {str(e)}", 500

# Edit paper route
@catalogue_routes.route('/edit_paper/<paper_id>', methods=['POST'])
def edit_paper(paper_id):
    paper = Paper.query.get(paper_id)

    if not paper:
        return jsonify({'success': False, 'message': 'Paper not found'}), 404

    try:
        paper.name = request.form.get('name')
        paper.description = request.form.get('description')

        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                paper.link = filename

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Paper updated successfully',
            'subject_name': paper.subject.name  # 👈 include this for redirect
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


#Add Subject  route 
@catalogue_routes.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        subject_description = request.form['subject_description']

        # Create a new subject record using SQLAlchemy
        new_subject = Subject(
            name=subject_name,
            description=subject_description
        )

        try:
            # Add the new subject to the database and commit
            db.session.add(new_subject)
            db.session.commit()

            # Redirect to the homepage (or another page)
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()  # Rollback in case of an error
            return f"Error adding subject: {str(e)}", 500

    return render_template('add_subject.html')


# Edit subject route
@catalogue_routes.route('/edit_subject/<subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    # Find the subject by ID
    subject = Subject.query.get(subject_id)

    if not subject:
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            # Update subject details with the new values from the form
            subject.name = request.form['name']
            subject.description = request.form['description']

            # Commit the changes to the database
            db.session.commit()
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()  # Rollback in case of an error
            return f"Error updating subject: {str(e)}", 500

    # For GET requests, render the form pre-filled with the current subject details
    return render_template('edit_subject.html', subject=subject)


# Delete subject route
@catalogue_routes.route('/delete_subject/<subject_id>', methods=['POST'])
def delete_subject(subject_id):
    # Find the subject by ID
    subject = Subject.query.get(subject_id)

    if not subject:
        return redirect(url_for('index'))

    try:
        # Delete the subject from the database
        db.session.delete(subject)
        db.session.commit()

    except Exception as e:
        db.session.rollback()  # Rollback in case of an error
        return f"Error deleting subject: {str(e)}", 500

    # Redirect back to the homepage after deletion
    return redirect(url_for('index'))
