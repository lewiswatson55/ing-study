import pandas as pd

# Load the CSV file
df = pd.read_csv('latestdata.csv')


# Function to check attention criteria
def check_attention_criteria(row):
    failed_checks = []
    count = 0

    for i in range(1, 31):  # Assuming there are 30 tasks (task1 to task30)
        item_id_col = f'item{i}_id'
        fluency_col = f'task{i}_fluency'
        allparts_col = f'task{i}_allparts'

        if row[item_id_col] == 'attn1':
            count += 1
            if row[fluency_col] != 1 or row[allparts_col] != 'missing,missing,missing':
                failed_checks.append(
                    (f'task{i}', 'attn1', row[fluency_col] != 1, row[allparts_col] != 'missing,missing,missing'))

        if row[item_id_col] == 'attn2':
            count += 1
            if row[fluency_col] != 5 or row[allparts_col] != 'incorrect,incorrect,incorrect':
                failed_checks.append(
                    (f'task{i}', 'attn2', row[fluency_col] != 5, row[allparts_col] != 'incorrect,incorrect,incorrect'))

    if failed_checks:
        return row['prolific_id'], failed_checks, count
    return None, [], count


# Apply the function to each row and collect failed prolific_ids and count attention checks
results = df.apply(check_attention_criteria, axis=1)
failed_ids = [(result[0], result[1]) for result in results if result[0] is not None]
attention_checks_count = sum(result[2] for result in results)

print("Failed Prolific IDs and Details of Failures:")
for prolific_id, failures in failed_ids:
    print(f"Prolific ID: {prolific_id}")
    for task, attn_type, fluency_failed, parts_failed in failures:
        failed_parts = []
        if fluency_failed:
            failed_parts.append("fluency")
        if parts_failed:
            failed_parts.append("parts")
        failed_parts_str = " and ".join(failed_parts)
        print(f" - Failed {attn_type} on {task} ({failed_parts_str})")

print(f"Total number of attention checks found: {attention_checks_count} - remember its two per task!")
