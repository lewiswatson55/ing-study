import pandas as pd
import re


# Define a function to extract SUBJECT, PREDICATE, and OBJECT
def extract_parts(input_string):
    subject_match = re.search(r"&lt;SUBJECT&gt; (.*?) &lt;", input_string)
    predicate_match = re.search(r"&lt;PREDICATE&gt; (.*?) &lt;", input_string)
    object_match = re.search(r"&lt;OBJECT&gt; (.*)", input_string)

    subject = subject_match.group(1) if subject_match else None
    predicate = predicate_match.group(1) if predicate_match else None
    object_ = object_match.group(1) if object_match else None

    return subject, predicate, object_


# Read the CSV file
df = pd.read_csv('fixed-example-for-lewis.csv')

# Create a list to hold the new column names in order
new_columns = []

# Process each item_input column and insert the new columns in order
for i in range(1, 6):
    col_name = f'item{i}_input'
    subject_col = f'item{i}_input_subject'
    predicate_col = f'item{i}_input_predicate'
    object_col = f'item{i}_input_object'

    df[subject_col], df[predicate_col], df[object_col] = zip(*df[col_name].map(extract_parts))

    # Find the index of the current item_input column
    col_index = df.columns.get_loc(col_name)

    # Insert the new columns right after the current item_input column
    new_columns.extend([subject_col, predicate_col, object_col])
    for new_col in reversed([subject_col, predicate_col, object_col]):
        df.insert(col_index + 1, new_col, df.pop(new_col))

# Save the processed DataFrame to a new CSV file
df.to_csv('processed_dataset.csv', index=False)

print("Extraction complete. Processed data saved to 'processed_dataset.csv'.")
