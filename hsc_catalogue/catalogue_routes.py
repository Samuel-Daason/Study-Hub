from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import json
import os
import uuid
from werkzeug.utils import secure_filename

# Define the blueprint
catalogue_routes = Blueprint('catalogue_routes', __name__)

# Path to the JSON file
# Define the absolute path to the JSON file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of the current Python file
JSON_FILE_PATH = os.path.join(BASE_DIR, 'data/catalogue.json')

# Define the absolute path to the static/papers folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'papers')

# Allowed file types (optional)
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'mp3', 'txt', 'doc', 'docx'}

# Load the JSON data
def load_data():
    with open(JSON_FILE_PATH, 'r') as file:
        return json.load(file)

# Helper function to save data to the JSON file
def save_data(data):
    with open(JSON_FILE_PATH, 'w') as file:
        json.dump(data, file, indent=4)

# Check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Add paper route
@catalogue_routes.route('/add_paper/<subject_name>', methods=['GET', 'POST'])
def add_paper(subject_name):
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        description = request.form['description']

        # Handle file upload
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            # Load current catalog data
            papers_data = load_data()

            # Prepare new paper data
            new_paper = {
                'id': str(uuid.uuid4()),  # Generate a unique UUID as a string
                'name': name,
                'description': description,
                'link': filename  # Store only the filename, since it's in the static/papers folder
            }

            # Add the new paper to the subject
            if subject_name in papers_data:
                papers_data[subject_name].append(new_paper)
            else:
                papers_data[subject_name] = [new_paper]

            # Save the updated data
            save_data(papers_data)

            # Redirect to the subject's page to see the newly added paper
            return redirect(url_for('catalogue_routes.view_papers', subject_name=subject_name))
        else:
            # Handle the case where the file extension is not allowed
            return "File type not allowed. Please upload a valid file.", 400

    return render_template('add_paper.html', subject_name=subject_name)

# View paper routes
@catalogue_routes.route('/<subject_name>')
def view_papers(subject_name):
    # Convert subject_name from URL format (e.g., "mathematics_advanced") to the format in JSON (e.g., "Mathematics Advanced")
    formatted_subject_name = subject_name.replace('_', ' ').title()

    # Load the papers data
    papers_data = load_data()

    # Get the papers for the given subject (ensuring the subject name matches the one in the JSON)
    subject_papers = papers_data.get(formatted_subject_name, [])

    return render_template('view_papers.html', subject_name=formatted_subject_name, papers=subject_papers)


# Edit paper route
@catalogue_routes.route('/edit_paper/<paper_id>', methods=['GET', 'POST'])
def edit_paper(paper_id):
    print(f"Received edit request for paper_id: {paper_id}")
    if request.method != 'POST':
        return jsonify({'success': False, 'message': 'Only POST method is allowed'}), 405

    try:
        # Load the current data
        papers_data = load_data()
        print(f"Loaded papers data, looking for paper {paper_id}")

        # Find the paper to edit
        paper = None
        subject_name = None

        # Iterate over the subjects to find the paper
        for subject, subject_papers in papers_data.items():
            if subject == 'subjects':  # Skip the subjects metadata section
                continue
            print(f"Checking subject: {subject}")
            for p in subject_papers:
                print(f"Comparing {str(p.get('id'))} with {str(paper_id)}")
                if str(p.get('id')) == str(paper_id):
                    paper = p
                    subject_name = subject
                    print(f"Found paper in subject {subject}")
                    break
            if paper:
                break

        if not paper:
            print(f"Paper {paper_id} not found")
            return jsonify({'success': False, 'message': f"Paper with ID {paper_id} not found."}), 404

        try:
            print("Processing POST request")
            print(f"Form data: {request.form}")
            print(f"Files: {request.files}")

            # Update paper details
            if 'name' not in request.form or 'description' not in request.form:
                return jsonify({'success': False, 'message': 'Name and description are required'}), 400

            paper['name'] = request.form.get('name')
            paper['description'] = request.form.get('description')
            print(f"Updated name to {paper['name']} and description to {paper['description']}")

            # Handle file upload if a new file is provided
            if 'file' in request.files:
                file = request.files['file']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    try:
                        file.save(file_path)
                        paper['link'] = filename  # Update with the new file
                        print(f"Saved new file: {filename}")
                    except Exception as e:
                        print(f"Error saving file: {str(e)}")
                        return jsonify({'success': False, 'message': f'Error saving file: {str(e)}'}), 500

            # Save the updated data
            try:
                save_data(papers_data)
                print("Saved updated data to file")
            except Exception as e:
                print(f"Error saving data: {str(e)}")
                return jsonify({'success': False, 'message': f'Error saving data: {str(e)}'}), 500

            return jsonify({'success': True, 'message': 'Paper updated successfully'})
        except Exception as e:
            print(f"Error in POST processing: {str(e)}")
            return jsonify({'success': False, 'message': f'Error processing request: {str(e)}'}), 500

    except Exception as e:
        print(f"Error in edit_paper route: {str(e)}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

# Delete paper route
@catalogue_routes.route('/delete_paper/<subject_name>/<paper_id>', methods=['POST'])
def delete_paper(subject_name, paper_id):
    # Load the current catalogue data from the JSON file
    papers_data = load_data()

    # Debugging: Print the subject papers and paper_id being used
    print(f"Subject: {subject_name}, Paper ID: {paper_id}")

    # Find and delete the paper with the given id
    for subject, subject_papers in papers_data.items():
        if subject == 'subjects':  # Skip the subjects metadata section
            continue

        paper_to_delete = next((paper for paper in subject_papers if paper['id'] == paper_id), None)
        if paper_to_delete:
            print(f"Found paper to delete: {paper_to_delete}")
            subject_papers.remove(paper_to_delete)
            break
        else:
            print(f"Paper with ID {paper_id} not found in subject {subject}")

    # Save the updated data back to the JSON file
    save_data(papers_data)

    # Redirect back to the subject's page after deletion
    return redirect(url_for('catalogue_routes.view_papers', subject_name=subject_name))

# Add subject route
@catalogue_routes.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        subject_description = request.form['subject_description']

        # Generate a unique ID for the new subject using UUID
        subject_id = str(uuid.uuid4())

        # Create the link dynamically based on the subject name
        subject_link = f"/{subject_name.replace(' ', '_').lower()}"

        # Load current catalogue data
        catalogue_data = load_data()

        # Prepare the new subject data
        new_subject = {
            'id': subject_id,  # Add the unique ID
            'name': subject_name,
            'description': subject_description,
            'link': subject_link  # This will now be generated in the backend
        }

        # Add the new subject to the catalogue
        if 'subjects' not in catalogue_data:
            catalogue_data['subjects'] = []
        catalogue_data['subjects'].append(new_subject)

        # Save the updated data
        save_data(catalogue_data)

        # Redirect to the homepage (or another page)
        return redirect(url_for('index'))

    return render_template('add_subject.html')

# Edit subject route
@catalogue_routes.route('/edit_subject/<subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    # Load the current catalogue data
    catalogue_data = load_data()

    # Find the subject to edit
    subject = next((s for s in catalogue_data['subjects'] if s['id'] == subject_id), None)

    if not subject:
        return f"Subject with ID {subject_id} not found.", 404

    if request.method == 'POST':
        # Update subject details with new values from the form
        subject['name'] = request.form['name']
        subject['description'] = request.form['description']

        # Save the updated catalogue data back to the JSON file
        save_data(catalogue_data)

        # Redirect to the index page after the update
        return redirect(url_for('index'))

    # Render the form pre-filled with the current subject details
    return render_template('edit_subject.html', subject=subject)

# Delete subject route
@catalogue_routes.route('/delete_subject/<subject_id>', methods=['POST'])
def delete_subject(subject_id):
    # Load the current catalogue data from the JSON file
    catalogue_data = load_data()

    # Find and delete the subject with the given id
    subject_to_delete = next((subject for subject in catalogue_data['subjects'] if subject['id'] == subject_id), None)
    if subject_to_delete:
        catalogue_data['subjects'].remove(subject_to_delete)
    else:
        return f"Subject with ID {subject_id} not found.", 404

    # Save the updated data back to the JSON file
    save_data(catalogue_data)

    # Redirect back to the homepage after deletion
    return redirect(url_for('index'))
