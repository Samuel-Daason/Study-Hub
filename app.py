from flask import Flask, render_template, send_from_directory, request, redirect
import json
import os
from catalogue_routes import catalogue_routes, view_papers, load_data  # Import the view_papers function

app = Flask(__name__)

# Determine the base directory of the application
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute path to the JSON file
CATALOGUE_PATH = os.path.join(BASE_DIR, 'data', 'catalogue.json')

# Load the JSON data globally so it can be accessed by the route functions
with open(CATALOGUE_PATH) as f:
    papers_data = json.load(f)

# Index route (display subjects)
@app.route('/', methods=['GET', 'POST'])
def index():
    # Load the catalogue data again (after any edits)
    catalogue_data = load_data()
    subjects = catalogue_data['subjects']

    if request.method == 'POST':
        # Print the form data to check if it's being received correctly
        print(f"Form Data: {request.form}")

        subject_name = request.form.get('subject_name')
        subject_description = request.form.get('subject_description')
        subject_id = request.form.get('subject_id')

        # Ensure form data is received correctly
        print(f"subject_name: {subject_name}, subject_description: {subject_description}")

        # Find the subject to update (use the subject's ID or name)
        updated_subject = {
            "name": subject_name,
            "description": subject_description
        }

        # Update the subject data in the catalogue
        for subject in subjects:
            if subject['id'] == subject_id:
                subject['name'] = subject_name
                subject['description'] = subject_description

        # Save the updated data back to the JSON file
        with open(CATALOGUE_PATH, 'w') as f:
            json.dump(catalogue_data, f, indent=4)

        # After adding the subject, redirect back to the index page
        return redirect('/')

    # Render the index page with the updated subjects
    return render_template('index.html', subjects=subjects)


# Register the catalogue blueprint with the app
app.register_blueprint(catalogue_routes, url_prefix='/catalog')


@app.route('/<subject_name>')
def subject_page(subject_name):
    return view_papers(subject_name)


@app.route('/scripts/<path:path>')
def send_js(path):
    return send_from_directory('scripts/js', path)


if __name__ == '__main__':
    app.run(debug=True)
