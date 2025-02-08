import pandas as pd

def load_users(file_path):
    try:
        df = pd.read_csv(file_path)
        if 'Username' not in df.columns:
            raise ValueError("CSV file is missing necessary 'Username'")
        return df
    except Exception as e:
        print(f"Failed to load users: {e}")
        return pd.DataFrame(columns=['Username'])

# Load the dataset containing thoughts
thoughts_csv = 'thoughts.csv'
all_thoughts = pd.read_csv(thoughts_csv, header=None).iloc[:, 0].tolist()

# Load user data
users_df = load_users('users.csv')

# Create sequential pairs of users
usernames = users_df['Username'].tolist()
user_pairs = [(usernames[i], usernames[i + 1]) for i in range(0, len(usernames) - 1, 2)]
print(user_pairs)
# Adjust for an odd number of users
if len(usernames) % 2 != 0:
    # Add the last user to a new pair if odd number of users
    user_pairs.append((usernames[-1], None))

# Define the number of thoughts assigned per user pair
thoughts_per_pair = 10  # Adjust as necessary based on the number of available thoughts

# Initialize a list to store the result
pairs_thoughts = []

# Iterate over each user pair
for index, (user1, user2) in enumerate(user_pairs):
    start_index = index * thoughts_per_pair
    end_index = start_index + thoughts_per_pair

    # Ensure we do not exceed the available thoughts
    if start_index >= len(all_thoughts):
        break

    # Adjust end_index if it goes beyond the list length
    end_index = min(end_index, len(all_thoughts))

    # Fetch the thoughts for the current pair
    thoughts_for_pair = all_thoughts[start_index:end_index]

    # Append the pair and their thoughts to the result list
    pairs_thoughts.append({
    'User 1': user1,
    'User 2': user2 if user2 else "",
    'Thoughts': '|'.join(str(x) for x in thoughts_for_pair)
})


# Convert the list to a DataFrame for better visualization and processing
pairs_thoughts_df = pd.DataFrame(pairs_thoughts)

# Save the updated DataFrame back to CSV
pairs_thoughts_df.to_csv('assigned_thoughts.csv', index=False)

print("Assigned thoughts CSV has been created successfully.")
