import sqlite3
import json
import pandas as pd

# Connect to the SQLite database
conn = sqlite3.connect('latest2.db')

# Query the data from the tables and join them based on the primary key
query = '''
    SELECT r.id, r.json_string, r.prolific_id, t.task_number, t.time_allocated, t.session_id, t.status
    FROM results r
    JOIN tasks t ON r.id = t.id
'''
df = pd.read_sql_query(query, conn)

# Close the database connection
conn.close()


def fix_json_string(json_string):
    # Replace all single quotes with double quotes
    json_string = json_string.replace("\"", '`')
    json_string = json_string.replace("'", '"')
    print(json_string)
    #input("Press Enter to continue...")
    return json_string


def parse_json(json_string):
    try:
        # Fix the JSON string formatting issues
        json_string = fix_json_string(json_string)
        data = json.loads(json_string)

        # Initialize a dictionary to store extracted data
        parsed_data = {}

        # Process each task-related item
        for key, value in data.items():
            if key.startswith('task') and isinstance(value, dict):
                task_num = key[4:]  # Extract the task number
                parsed_data[f'task{task_num}_fluency'] = value.get('fluency', '')

                parts = value.get('parts', [])
                # Store parts as a comma-separated string
                parsed_data[f'task{task_num}_allparts'] = ','.join(parts)

        # Additional fields, assuming they are not nested within dictionaries
        parsed_data['task_id'] = data.get('task_id', '')
        parsed_data['prolific_pid'] = data.get('prolific_pid', '')
        parsed_data['session_id'] = data.get('session_id', '')

        return pd.Series(parsed_data)

    except Exception as e:
        # Print the problematic JSON string and the error message for debugging
        print(f"Failed to parse JSON string: {json_string}")
        print(f"Error: {str(e)}")
        return pd.Series()


# Apply the parsing function to the 'json_string' column
parsed_df = df['json_string'].apply(parse_json)

# Concatenate the parsed data with the original DataFrame
df = pd.concat([df.drop('json_string', axis=1), parsed_df], axis=1)

# Save the DataFrame as a CSV file
#df.to_csv('combined_results.csv', index=False)

# Read the combined_results.csv file
combined_df = df

# Read the authors_data.csv file
authors_df = pd.read_csv('e2e-humeval5.csv')

# Reset the index of authors_df to start from 1 instead of 0
authors_df.reset_index(inplace=True)
authors_df['index'] += 1  # Adjust the index to start from 1
authors_df.rename(columns={'index': 'task_number'}, inplace=True)

# Ensure the 'task_number' columns in both dataframes are of the same data type
combined_df['task_number'] = combined_df['task_number'].astype(int)
authors_df['task_number'] = authors_df['task_number'].astype(int)

# Merge the dataframes based on the 'task_number' column
merged_df = pd.merge(combined_df, authors_df, on='task_number', how='left')

# Save the merged dataframe to a new file called full_data.csv
merged_df.to_csv('latestdata.csv', index=False)
