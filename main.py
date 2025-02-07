# This is the webapp for hosting Prolific surveys for the Edinburgh Napier University lab within the reprohum project.
# The data is in csv format, containing the data from the survey. File name should be DATA variable
# The user interface is the interface.html file, which is a template for the survey.
# Each interface has the following structure ${outputb1} where inside the brackets is the name of the variable.
# There can be multiple variables - which should be defined in the python code to match the variable names in the csv file.
import json
from datetime import datetime

import requests
from flask import Flask, render_template, request, redirect, url_for, render_template_string, abort, jsonify
import csv
import pandas as pd
import re
import uuid as uuid_lib
import os

import pprint
pp = pprint.PrettyPrinter(indent=4)

import DataManager as dm

MAX_TIME = 5220  # 5220 = 87 minutes Maximum time in seconds that a task can be assigned to a participant before it is abandoned - 1 hour = 3600 seconds
                 # Should probably note the 1hr limit on the interface/instructions.
                 # NOTE: If you do not want to expire tasks, set this to a very large number, 0 will not work.

CHECK_TIME = 30  # Time in seconds between checks for abandoned tasks - 1 hour = 3600 seconds

PASSWORD = "password"  # Password for the /tasksallocated route
TEMPLATE = "humevaljinja.html"
DATA = "e2e-humeval.csv"
#DATA = "example-for-lewis.csv"
NUMOFITEMS = 30
# Load the data from the csv file into a pandas dataframe
df = pd.read_csv(DATA)
# Create a list of the column names in the csv file
column_names = df.columns.values.tolist()

# Create a dictionary of tasks, where each task is a row in the csv file
# This should probably be saved to a file rather than in memory, so that we can restart the server and not lose data.
#tasks = {i: {"completed_count": 0, "participants": [], "assigned_times": []} for i in range(len(df))}

# TODO: Might require adding CORS headers to allow requests. See https://flask-cors.readthedocs.io/en/latest/
app = Flask(__name__,
    static_url_path='', 
    static_folder='static',
    template_folder='templates') # Create the flask app

# MTurk template replacement tokens is different to Jinja2, so we just do it manually here.
def preprocess_html(html_content, df, task_id=-1):

    for column_name in column_names:
        html_content = html_content.replace("${"+column_name+"}", str(df[column_name].values[0]))

    html_content = html_content.replace("${task_id}", str(task_id))

    return html_content




# Routes

# This is the index route, which will just say nothing here. If it gets a POST request, it will save the HIT response JSON to a file.
# NOTE: The HTML interfaces should be updated with a button that compiles the answers as a JSON object and POSTS to this app.
# TODO: Validate submission is JSON and has required fields (task_id, prolific_pid, etc) else could crash
@app.route('/inlg', methods=['POST'])
@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':
        # Print JSON from POST request
        pp.pprint(request.json)

        # Save JSON to file with task_id as the folder and uuid as the filename
        task_id = request.json['task_id']
        prolific_pid = request.json['prolific_pid']
        folder_path = os.path.join('data', str(task_id))
        os.makedirs(folder_path, exist_ok=True)  # Create folder if it doesn't exist

        file_path = os.path.join(folder_path, f"{task_id}.json")

        with open(file_path, 'w') as outfile:
            json.dump(request.json, outfile)

        # Complete the task
        print(task_id, request.json, prolific_pid)

        complete = dm.complete_task(task_id, str(request.json), prolific_pid)

        if complete == -1:
            return {"result":"Something went wrong? Is this your task?"}, 500

        return {"result":"OK"}, 200
    else:
        return "Nothing Here.", 200


@app.route('/eval')
def eval():
    return render_template(TEMPLATE)

def split_input(input_str):
    triples = []
    parts = input_str.split('<')
    parts = [part.strip() for part in parts if part]  # Remove empty strings and strip whitespace

    #print(parts)

    if len(parts) % 3 != 0:
        raise ValueError("The input string does not contain a valid number of triples.")

    for i in range(0, len(parts), 3):
        try:
            subject = parts[i].replace('SUBJECT> ', '')
            predicate = parts[i + 1].replace('PREDICATE> ', '')
            object_ = parts[i + 2].replace('OBJECT> ', '')
            triples.append((subject, predicate, object_))
        except IndexError:
            raise ValueError("The input string does not contain a valid number of triples.")
    return triples


@app.route('/e/<int:row_id>')
def e(row_id):
    row = df.iloc[row_id]
    items = []
    print("Row length " + str(len(row)))
    for i in range(1, NUMOFITEMS+1):  # Adjust the range based on the maximum number of items
        item_input_key = f'item{i}_input'
        if item_input_key in row:
            triples = split_input(row[item_input_key])
            items.append({
                'triples': triples,
                'text': row[f'item{i}_text']
            })
        else:
            print(f"item {item_input_key} not found in row {row_id}... skipping.")
    # print(items)
    # print(len(items))
    return render_template(TEMPLATE, items=items)

# This route is used for testing the interface on specific rows of the csv file
@app.route('/row/<int:row_id>', methods=['GET', 'POST'])
def row(row_id):
    # Read the HTML template file
    with open(f'templates/{TEMPLATE}', 'r') as html_file:
        html_content = html_file.read()
    # Preprocess the HTML content
    processed_html = preprocess_html(html_content, df.iloc[[row_id]], row_id)
    return render_template_string(processed_html)


@app.route('/study/')
def study():

    # Get PROLIFIC_PID, STUDY_ID and SESSION_ID from URL parameters
    prolific_pid = request.args.get('PROLIFIC_PID')
    session_id = request.args.get('SESSION_ID')
    study_id = request.args.get('STUDY_ID')

    # Read the HTML template file
    with open(f'templates/{TEMPLATE}', 'r') as html_file:
        html_content = html_file.read()

    # Allocate task or find already allocated task
    if prolific_pid is None or session_id is None:
        return "PROLIFIC_PID and SESSION_ID are required parameters.", 400
    else:
        task_id, task_number = dm.allocate_task(prolific_pid, session_id)

    # If there is a database error, return the error message and status code
    if task_id == "Database Error - Please try again, if the problem persists contact us." and task_number == -1:
        return task_id, 500

    # If no task is available, return a message
    if task_id is None:
        return "No tasks available - if this is unexpected please wait up to 1 minute and refresh the page.", 400

    # Process the task content
    row = df.iloc[task_number - 1]
    items = []
    for i in range(1, NUMOFITEMS + 1):  # Adjust the range based on the maximum number of items
        item_input_key = f'item{i}_input'
        if item_input_key in row:
            triples = split_input(row[item_input_key])
            items.append({
                'triples': triples,
                'text': row[f'item{i}_text']
            })

    # Render the template with Jinja
    return render_template(TEMPLATE, items=items, prolific_pid=prolific_pid, session_id=session_id, study_id=study_id, task_id=task_id)


# This route is used for testing - it will return the tasks dictionary showing the number of participants assigned to each task
@app.route('/tasksallocated')
def allocated():
    password = request.args.get('password')
    if password != PASSWORD:
        abort(403)  # Forbidden

    tasks = dm.get_all_tasks()
    return jsonify(tasks)

# Show a specific task_id's result in the database
@app.route('/results/<task_id>')
def results(task_id):
    result = dm.get_specific_result(str(task_id))
    if result is None:
        return "No result found for task_id: " + str(task_id), 400
    return str(result)


# Check for tasks that have been assigned for more than 1 hour and then open them up again for participants to complete. Code at bottom of file will make this run every hour.
# The route is set up for testing to manually check for abandoned tasks. It will return a list of abandoned tasks that have been opened up again.
@app.route('/abdn')
def check_abandonment():
    password = request.args.get('password')
    if password != PASSWORD:
        abort(403)  # Forbidden

    print("Force checking for abandoned tasks...")
    dm.expire_tasks(MAX_TIME)  # Do not update MAX_TIME manually, use MAX_TIME variable
    tasks = dm.get_all_tasks()
    return jsonify(tasks)

def check_abandonment_auto():
    print("Checking for abandoned tasks...")
    dm.expire_tasks(MAX_TIME)  # Do not update MAX_TIME manually, use MAX_TIME variable


# Scheduler

# Run the check_abandonment function every hour - this has to be before the app.run() call
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_abandonment_auto, trigger="interval", seconds=CHECK_TIME) # Do not update seconds manually, use MAX_TIME
scheduler.start()

# @app.route('/inlg', methods=['POST'])
# def inlg():
#     data = request.get_json()
#     print(data)
#     return {"result":"ok"}, 200

# CLI Entry Point (for testing) - python main.py

@app.route('/webhook-handler', methods=['POST'])
def webhook_handler():
    try:
        event = request.json
        if event and event.get('event') == 'submission.returned':
            # Extract relevant data from the event
            returned_submission = event.get('data', {})
            participant_id = returned_submission.get('participant_id')
            if participant_id:
                print("Returned PID:", participant_id)
                # Clear tasks for the returned participant
                dm.clear_tasks_for_prolific_pids([participant_id])
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'ignored', 'message': 'No relevant event'}), 200
    except Exception as e:
        print("Error handling webhook:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

