from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, Request
from models import db, Subject, Paper, User, PaperNote
import os
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import random
from datetime import datetime, timedelta

from dotenv import load_dotenv
import os

# Load env from .env
load_dotenv()
# Get the SendGrid API Key from the environment
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")



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


# View paper routes
@catalogue_routes.route('/<subject_name>')
def view_papers(subject_name):
    # Query the subject by name, case-sensitive (or adjust as needed)
    subject = Subject.query.filter_by(name=subject_name).first_or_404()

    # Query papers related to the subject
    papers = Paper.query.filter_by(subject_id=subject.id).all()

    # Render the template with the subject name and the list of papers
    return render_template('view_papers.html', subject_name=subject_name, papers=papers)


# Add paper route
@catalogue_routes.route('/add_paper/<subject_name>', methods=['GET', 'POST'])
@login_required  # Make sure only logged-in users can add papers
def add_paper(subject_name):
    subject = Subject.query.filter_by(name=subject_name).first_or_404()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        file = request.files['file']

        if not name or not description or not file:
            return "All fields (name, description, and file) are required.", 400

        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)

                new_paper = Paper(
                    name=name,
                    description=description,
                    link=filename,
                    subject_id=subject.id,
                    user_id=current_user.id 
                )
                db.session.add(new_paper)
                db.session.commit()

                return redirect(url_for('catalogue_routes.view_papers', subject_name=subject_name))
            except Exception as e:
                db.session.rollback()
                return f"An error occurred while saving the paper: {str(e)}", 500
        else:
            return "Invalid file type. Please upload a valid file.", 400

    return render_template('add_paper.html', subject_name=subject_name)


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

# Edit Paper Route 
@catalogue_routes.route('/edit_paper/<int:paper_id>', methods=['POST'])
def edit_paper(paper_id):
    paper = Paper.query.get(paper_id)

    if not paper:
        return jsonify({'success': False, 'message': 'Paper not found'}), 404

    try:
        # Get name and description from form
        name = request.form.get('name')
        description = request.form.get('description')

        # Validate name and description
        if not name or not description:
            return jsonify({'success': False, 'message': 'Name and description are required'}), 400

        # Update the paper's name and description
        paper.name = name
        paper.description = description

        # Handle file upload (if provided)
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                paper.link = filename
            elif file.filename:  # Invalid file type case
                return jsonify({'success': False, 'message': 'Invalid file type'}), 400

        # Commit the changes to the database
        db.session.commit()

        # Log the success response before returning
        print("Paper updated successfully", paper)

        # Return success response with relevant data
        return jsonify({
            'success': True,
            'message': 'Paper updated successfully',
            'paper_id': paper.id,   # Include the paper ID in the response
            'paper_name': paper.name, # Include updated paper name
            'paper_description': paper.description, # Include updated description
            'paper_link': paper.link # Include the link if changed
        }), 200

    except Exception as e:
        db.session.rollback()

        # Log the exception to check what went wrong
        print(f"Error: {str(e)}")

        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500



# Add Subject route
@catalogue_routes.route('/add_subject', methods=['GET', 'POST'])
@login_required  # Ensure the user is logged in
def add_subject():
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        subject_description = request.form['subject_description']

        # Create a new subject record using SQLAlchemy
        new_subject = Subject(
            name=subject_name,
            description=subject_description,
            user_id=current_user.id  # Associate the subject with the current logged-in user
        )

        try:
            # Add the new subject to the database and commit
            db.session.add(new_subject)
            db.session.commit()

            # Redirect to the homepage (or another page)
            flash("Subject added successfully!")
            return redirect(url_for('catalogue_routes.index'))  # Ensure correct URL for the index page

        except Exception as e:
            db.session.rollback()  # Rollback in case of an error
            flash(f"Error adding subject: {str(e)}")
            return redirect(url_for('catalogue_routes.index'))  # Redirect back to the index page

    return render_template('add_subject.html')


# Edit Subject Route 
@catalogue_routes.route('/edit_subject/<subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    subject = Subject.query.get(subject_id)

    if not subject:
        return redirect(url_for('catalogue_routes.index'))  # Redirect if subject doesn't exist

    if request.method == 'POST':
        try:
            # Update subject details with the new values from the form
            subject.name = request.form['subject_name']
            subject.description = request.form['subject_description']

            # Commit the changes to the database
            db.session.commit()

            return redirect(url_for('catalogue_routes.index'))  # Redirect to index after saving changes

        except Exception as e:
            db.session.rollback()  # Rollback in case of an error
            return f"Error updating subject: {str(e)}", 500

    # For GET requests, render the form pre-filled with the current subject details
    return render_template('index.html', subject=subject)




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
    return redirect(url_for('catalogue_routes.index'))


# Login Route - Handles both login and redirects for logged-in users
@catalogue_routes.route('/login', methods=['GET', 'POST'])
def login():
    # If the user is already logged in, redirect to the index page
    if current_user.is_authenticated:
        return redirect(url_for('catalogue_routes.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Query the user from the database
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):  # Check if user and password match
            login_user(user)  # Log the user in
            print(f"User {user.email} logged in!")  # Debugging line
            return redirect(url_for('catalogue_routes.index'))  # Redirect to the dashboard

        flash("Invalid login credentials. Please try again.", "error")  # Show error if login fails

    return render_template('login.html')  # Show login form


# Make sure the user is logged in before viewing a page 
@catalogue_routes.route('/')
@login_required
def index():
    # Query the subjects that belong to the logged-in user
    user_subjects = Subject.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', subjects=user_subjects)


# Registration route
@catalogue_routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')  # Get email from form
        password = request.form.get('password')  # Get password from form
        confirm_password = request.form.get('confirm_password')  # Get confirm password from form

        form_errors = {}  # Dictionary to hold the form errors

        # Check if the passwords match
        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            form_errors['password'] = True
            form_errors['confirm_password'] = True
            return render_template('register.html', form_errors=form_errors)  # Return form with errors

        hashed_password = generate_password_hash(password)  # Hash the password

        # Check if the email is already registered
        existing_user = User.query.filter_by(email=email).first()  # Query by email
        if existing_user:
            flash("User already exists. Please login.", "error")
            return redirect(url_for('catalogue_routes.login'))  # Redirect to login if user exists

        # Create new user with email and hashed password
        new_user = User(email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Log the user in automatically after registration
        flash("Registration successful. Please log in.", "success")  # Flash success message
        return redirect(url_for('catalogue_routes.login'))  # Redirect to login page

    return render_template('register.html')  # Show registration form


# Logout route
@catalogue_routes.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()  # Log the user out
    return redirect(url_for('catalogue_routes.login'))  # Redirect to the login page


# Forgot Password route 
@catalogue_routes.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("That account doesn't exist.", 'error')
            return redirect(url_for('catalogue_routes.forgot_password'))

        # Generate a 6-digit reset code
        reset_code = str(random.randint(100000, 999999))

        # Store the reset code and timestamp
        user.reset_code = reset_code
        user.reset_code_sent_at = datetime.utcnow()
        db.session.commit()

        # Send the reset email with the reset code
        send_reset_email(user.email, reset_code)

        # flash('A password reset link has been sent to that email adress.', 'info')  # Removed as requested
        return redirect(url_for('catalogue_routes.verify_code', email=email))

    return render_template('forgot_password.html')


# Send Email Route
def send_reset_email(to_email, reset_code):
    if not SENDGRID_API_KEY:
        raise ValueError("SendGrid API Key is not set.")  # Ensure there's a valid key

    try:
        # Create SendGrid client instance
        sg = SendGridAPIClient(SENDGRID_API_KEY)

        # Set the email details
        from_email = Email("sdaason@students.rj.nsw.edu.au")
        subject = "Password Reset Request"
        content = Content("text/plain", f"Here is your password reset code: {reset_code}\nIt will expire in 5 minutes.")
        to_email = To(to_email)

        # Create and send the mail
        mail = Mail(from_email, to_email, subject, content)
        response = sg.client.mail.send.post(request_body=mail.get())

        # Return the response
        return response
    except Exception as e:
        print(f"Error sending email: {e}")  # Print any exception error message
        return None


# Verify 6 Digit Code 
@catalogue_routes.route('/verify_code', methods=['GET', 'POST'])
def verify_code():
    email = request.args.get('email')
    user = User.query.filter_by(email=email).first()

    if not user:
        flash("Invalid or expired reset link.", "error")
        return redirect(url_for('catalogue_routes.forgot_password'))

    if request.method == 'POST':
        code_entered = request.form.get('reset_code')

        if user.reset_code != code_entered:
            flash("Incorrect code.", "error")
        elif datetime.utcnow() > user.reset_code_sent_at + timedelta(minutes=5):
            flash("Code expired. Please resend.", "error")
        else:
            flash("Code verified! You may now reset your password.", "success")
            return redirect(url_for('catalogue_routes.reset_password', email=email))

    return render_template('verify_code.html', email=email)


# Resend Code Route
@catalogue_routes.route('/resend_code')
def resend_code():
    email = request.args.get('email')
    user = User.query.filter_by(email=email).first()

    if not user:
        flash("That account doesn't exist.", 'error')
        return redirect(url_for('catalogue_routes.forgot_password'))

    # Check if the previous reset code has expired
    if datetime.utcnow() > user.reset_code_sent_at + timedelta(minutes=5):
        # Generate a new reset code and update timestamp
        reset_code = str(random.randint(100000, 999999))
        user.reset_code = reset_code
        user.reset_code_sent_at = datetime.utcnow()
        db.session.commit()

        # Resend the email
        send_reset_email(user.email, reset_code)
        flash("A new code has been sent to your email.", 'info')
    else:
        flash("Please wait before requesting a new code.", 'warning')

    return redirect(url_for('catalogue_routes.verify_code', email=email))



# Reset Password Route
@catalogue_routes.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    email = request.args.get('email')
    user = User.query.filter_by(email=email).first()

    if not user:
        flash("Invalid reset attempt.", 'error')
        return redirect(url_for('catalogue_routes.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash("Passwords do not match.", 'error')
            return redirect(url_for('catalogue_routes.reset_password', email=email))

        # Use set_password to hash the password
        user.set_password(password)
        user.reset_code = None
        user.reset_code_sent_at = None
        db.session.commit()

        flash("Your password has been reset. You can now log in.", 'success')
        return redirect(url_for('catalogue_routes.login'))

    return render_template('reset_password.html', email=email)


#Dashbaord Route
@catalogue_routes.route('/dashboard')
@login_required
def dashboard():
    # Only get subjects that belong to the current user
    subjects = Subject.query.filter_by(user_id=current_user.id).all()

    subject_data = []
    for subject in subjects:
        # Count papers linked to each subject
        paper_count = Paper.query.filter_by(subject_id=subject.id, user_id=current_user.id).count()
        subject_data.append({
            'name': subject.name,
            'paper_count': paper_count
        })

    return render_template('dashboard.html', subject_data=subject_data)


# Add Notes Route
@catalogue_routes.route('/add_note', methods=['POST'])
@login_required
def add_note():
    paper_id = request.form.get('paper_id')
    time_spent = request.form.get('time_spent')
    score = request.form.get('score')
    difficulty_rating = request.form.get('difficulty_rating')
    difficult_questions = request.form.get('difficult_questions')

    if not all([paper_id, time_spent, score, difficulty_rating]):
        # No flash here, just redirect
        return redirect(url_for('catalogue_routes.index'))

    try:
        note = PaperNote(
            user_id=current_user.id,
            paper_id=int(paper_id),
            time_spent=int(time_spent),
            score=int(score),
            difficulty_rating=int(difficulty_rating),
            difficult_questions=difficult_questions
        )
        db.session.add(note)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)

    # Lookup the paper to get its subject name for redirect
    paper = Paper.query.get(int(paper_id))
    if paper:
        subject = Subject.query.get(paper.subject_id)
        if subject:
            return redirect(url_for('catalogue_routes.view_papers', subject_name=subject.name))
    # Fallback redirect
    return redirect(url_for('catalogue_routes.index'))