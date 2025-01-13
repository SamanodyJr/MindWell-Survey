import streamlit as st
import pandas as pd

thoughts_csv = 'thoughts.csv'
all_thoughts = pd.read_csv(thoughts_csv, header=None).iloc[:, 0].tolist()  # Assuming thoughts are in the first column
thoughts_per_user = 5
assigned_thoughts = 'assigned_thoughts.csv'
ongoing_responses_file = 'responses.csv'
def get_user_thoughts(username):
    assigned_thoughts_df = pd.read_csv(assigned_thoughts)
    user_row = assigned_thoughts_df[assigned_thoughts_df['Username'] == username]
    if not user_row.empty:
        return user_row['Thoughts'].values[0].split('|')

    num_assigned = len(assigned_thoughts_df) * thoughts_per_user
    start_index = num_assigned
    end_index = start_index + thoughts_per_user

    if start_index >= len(all_thoughts):
        st.error("No more thoughts available to assign.")
        return []
    st.session_state.start_index = start_index
    st.session_state.end_index = end_index
    selected_thoughts = all_thoughts[start_index:end_index]
    new_row = pd.DataFrame([[username, '|'.join(selected_thoughts)]], columns=['Username', 'Thoughts'])
    assigned_thoughts_df = pd.concat([assigned_thoughts_df, new_row], ignore_index=True)
    assigned_thoughts_df.to_csv(assigned_thoughts, index=False)

    return selected_thoughts
def load_usernames():
    try:
        df = pd.read_csv('users.csv')
        if 'Username' not in df.columns or 'Password' not in df.columns:
            raise ValueError("CSV file is missing necessary 'Username' or 'Password' columns.")
        return df
    except Exception as e:
        st.error(f"Failed to load users: {e}")
        return pd.DataFrame(columns=['Username', 'Password'])

users = load_usernames()

def save_response(username, thought, label, agree=None):
    # Load existing data if available.
    try:
        responses_df = pd.read_csv(ongoing_responses_file)
    except FileNotFoundError:
        responses_df = pd.DataFrame(columns=['Username', 'Thought', 'Label', 'Agree'])

    # Update if the thought already exists or append a new one.
    mask = (responses_df['Username'] == username) & (responses_df['Thought'] == thought)
    if responses_df[mask].empty:
        new_row = pd.DataFrame([[username, thought, label, agree]], columns=['Username', 'Thought', 'Label', 'Agree'])
        responses_df = pd.concat([responses_df, new_row], ignore_index=True)
    else:
        responses_df.loc[mask, 'Label'] = label
        if agree is not None:
            responses_df.loc[mask, 'Agree'] = agree

    responses_df.to_csv(ongoing_responses_file, index=False)

def clear_responses(username):
    try:
        responses_df = pd.read_csv(ongoing_responses_file)
        responses_df = responses_df[responses_df['Username'] != username]
        responses_df.to_csv(ongoing_responses_file, index=False)
    except FileNotFoundError:
        pass

def load_responses(username):
    try:
        responses_df = pd.read_csv(ongoing_responses_file)
        user_responses = responses_df[responses_df['Username'] == username]
        return {row['Thought']: {'label': row['Label'], 'agree': row['Agree']} for index, row in user_responses.iterrows()}
    except FileNotFoundError:
        return {}

if 'username' not in st.session_state:
    st.session_state.username = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'consent_given' not in st.session_state:
    st.session_state.consent_given = False
if 'responses' not in st.session_state:
    st.session_state.responses = {}
if 'registration_success' not in st.session_state:
    st.session_state.registration_success = False
if 'nextsection_done' not in st.session_state:
    st.session_state.nextsection_done = False
if 'start_index' not in st.session_state:
    st.session_state.start_index = None
if 'end_index' not in st.session_state:
    st.session_state.end_index = None
if 'gpt_agreements' not in st.session_state:
    st.session_state.gpt_agreements = {}
def storeage():
    username = st.session_state.username
    age_group = st.session_state.age_group
    users_df = pd.read_csv('users.csv')
    user_index = users_df[users_df['Username'] == username].index
    if not user_index.empty:
        users_df.loc[user_index, 'Age'] = age_group
        users_df.to_csv('users.csv', index=False)
    age_groups = ["24-34", "35-44", "45-55", "55+"]
    st.session_state.age_group_index = age_groups.index(age_group)

def storeyear():
    username = st.session_state.username
    years_of_experience = st.session_state.years_of_experience
    users_df = pd.read_csv('users.csv')
    user_index = users_df[users_df['Username'] == username].index
    if not user_index.empty:
        users_df.loc[user_index, 'Experience'] = years_of_experience
        users_df.to_csv('users.csv', index=False)
    experience_levels = ["Below a year", "1-3 years", "4-7 years", "8-11 years", "12+ years"]
    st.session_state.years_of_experience_index = experience_levels.index(years_of_experience)
def update_consent():
    user_response = st.session_state.consent
    if user_response == 'Yes, I give my consent.':
        st.session_state.consent_given = True
    else:
        st.session_state.consent_given = False

def register_user(username, password):
    new_user = pd.DataFrame([[username, password]], columns=['Username', 'Password'])
    updated_users = pd.concat([users, new_user], ignore_index=True)
    updated_users.to_csv('users.csv', index=False)
    st.session_state.registration_success = True
def login(username,password):

    user_record = users[users['Username'] == username]
    if not user_record.empty and user_record.iloc[0]['Password'] == password:
        if user_record.iloc[0]['Submitted'] == 1:  # Check if the survey was already submitted
            st.success("Thank you! You have already completed the survey.")
            return
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.user_thoughts = get_user_thoughts(username)
        st.session_state.responses = load_responses(username)
        st.success(f"Welcome to our survey, {st.session_state.username}!")
        user_info = users[users['Username'] == username].iloc[0]
        age_groups = ["24-34", "35-44", "45-55", "55+"]
        years_of_experience_levels = ["Below a year", "1-3 years", "4-7 years", "8-11 years", "12+ years"]
        fields_of_interest = ["Counseling","Clinical Psychology","Therapy","Other"]
        # Set age group index if age is saved
        if pd.notna(user_info['Age']) and user_info['Age'] in age_groups:
            st.session_state.age_group = user_info['Age']
            st.session_state.age_group_index = age_groups.index(user_info['Age'])

        # Set years of experience index if experience is saved
        if pd.notna(user_info['Experience']) and user_info['Experience'] in years_of_experience_levels:
            st.session_state.years_of_experience = user_info['Experience']
            st.session_state.years_of_experience_index = years_of_experience_levels.index(user_info['Experience'])

        if pd.notna(user_info['Interest']):
            if user_info['Interest'] in fields_of_interest:
                st.session_state.field_interest = user_info['Interest']
                st.session_state.field_interest_index = fields_of_interest.index(user_info['Interest'])
            else:
                st.session_state.field_interest = user_info['Interest']
                st.session_state.field_interest_index = len(fields_of_interest) - 1

    else:
        st.error("Invalid username or password. Please try again.")

def register(username,password):
    if not username or not password:
        st.error("Both username and password are required to register.")
    elif username in users['Username'].values:
        st.error("Username already exists. Try another one.")
    else:
        new_user = pd.DataFrame([[username, password, 0]], columns=['Username', 'Password', 'Submitted'])
        updated_users = pd.concat([users, new_user], ignore_index=True)
        updated_users.to_csv('users.csv', index=False)
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.user_thoughts = get_user_thoughts(username)
        st.success(f"Welcome to our survey, {st.session_state.username}!")

def update_submission_status(username):
    users_df = pd.read_csv('users.csv')
    user_index = users_df[users_df['Username'] == username].index
    if not user_index.empty:
        users_df.loc[user_index, 'Submitted'] = 1
        users_df.to_csv('users.csv', index=False)
def load_gpt_labels():
    try:
        gpt_labels_df = pd.read_csv('gpt_labeled.csv')
        return dict(zip(gpt_labels_df['Thought'], gpt_labels_df['Label']))
    except FileNotFoundError:
        st.error("GPT labels file not found.")
        return {}

# Function for loading user responses
def load_user_labels(username):
    try:
        responses_df = pd.read_csv(ongoing_responses_file)
        user_responses = responses_df[responses_df['Username'] == username]
        return dict(zip(user_responses['Thought'], user_responses['Label']))
    except FileNotFoundError:
        st.error("User responses file not found.")
        return {}

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center; color: grey;'>Mindwell Survey</h2>", unsafe_allow_html=True)

    # Login/Register Box Styling
    st.markdown("""
        <style>
            .box {
                background-color: #f9f9f9;
                padding: 2px;
                border-radius: 10px;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
            }
            .btn {
                margin: 10px;
            }
        </style>
        """, unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="box">', unsafe_allow_html=True)
        username_input = st.text_input("Username:")
        password_input = st.text_input("Password:", type="password")
        col1, col2 = st.columns([0.92,1])
        with col1:
            st.button('Login',on_click=login, args=(username_input, password_input), use_container_width=True)
        with col2:
            st.button('Register', on_click=register, args=(username_input, password_input),use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.registration_success or st.session_state.logged_in:
    if not st.session_state.consent_given:
        st.header("Mindwell Survey")
        st.subheader("MindWell is a project dedicated to gathering data on several types of cognitive distortions. We’re harnessing the power of artificial intelligence to detect and classify cognitive distortions from written text. Your participation is crucial in building a diverse dataset that will not only serve the community but also facilitate the development of applications designed to enhance awareness of cognitive distortions.")
        st.write("This survey will take less than 10 minutes to complete.")

        consent = st.radio(
            "Do you give your consent for your responses to be collected and used for research purposes?",
            ('Yes, I give my consent.', 'No, I do not give my consent.'),
            index=None,  # No option is selected by default
            on_change = update_consent,  # Call update_consent when an option is selected
            key = 'consent'  # Key to maintain state of this specific widget
        )

    # If consent is given, display new content
    if st.session_state.consent_given:
        st.write("Thank you for your consent.")
        st.markdown("## Survey Questions")
        # Example of further survey questions
        # age = st.slider("Select your age", 25, 80)
        default_age_index = st.session_state.get('age_group_index', None)
        default_experience_index = st.session_state.get('years_of_experience_index', None)
        age_group = st.radio(
            "Select your age group:",
            ["24-34", "35-44", "45-55", "55+"],
            key='age_group', index=default_age_index,
            on_change=storeage
        )
        # years = st.slider("Years of Experience", 1, 30)
        years_of_experience = st.radio(
            "Select your years of experience:",
            ["Below a year", "1-3 years", "4-7 years", "8-11 years", "12+ years"],
            key='years_of_experience', index=default_experience_index,
            on_change=storeyear
        )
        st.header("Cognitive Distortions")
        st.markdown("""
        A form of recurring pattern in thoughts that leads to a negative bias in how an individual perceives different situations. These thoughts often stem from internal biases or misconceptions and can lead to mental health issues such as anxiety, depression, and low self-esteem.
        """)
        st.markdown("The types that we are targeting are:")
        distortions_data = {
            "Type of Cognitive Distortion": [
                "All or Nothing Thinking",
                "Fortune telling (also called catastrophizing)",
                "Emotional reasoning",
                "Labeling",
                "Mental Filter",
                "Mind reading",
                "Overgeneralization",
                "Personalization",
                "Should statements (also 'musts', 'oughts', 'have tos')",
                "Blaming (others or oneself)",
                "Discounting the positive",
                "Control fallacies",
                "Fallacy of Fairness",
                "Always being right"
            ],
            "Definition": [
                "I view a situation, a person or an event in 'either-or' terms, fitting them into only two extreme categories instead of on a continuum.",
                "I predict the future in negative terms and believe that what will happen will be so awful that I will not be able to stand it.",
                "I believe my emotions reflect reality and let them guide my attitudes and judgments.",
                "I put a fixed, global label, usually negative, on myself or others.",
                "I pay attention to one or a few details and fail to see the whole picture.",
                "I believe that I know the thoughts or intentions of others (or that they know my thoughts or intentions) without having sufficient evidence.",
                "I take isolated negative cases and generalize them, transforming them in a never-ending pattern, by repeatedly using words such as 'always', 'never', 'ever', 'whole', 'entire', etc.",
                "I assume that others' behaviors and external events concern (or are directed to) myself without considering other plausible explanations.",
                "I tell myself that events, people’s behaviors, and my own attitudes 'should' be the way I expected them to be and not as they really are.",
                "I direct my attention to others as sources of my negative feelings and experiences, failing to consider my own responsibility, or conversely, I take responsibility for others' behaviors and attitudes.",
                "I disqualify positive experiences or events insisting that they do not count.",
                "I feel that I am either externally controlled by others or situations, or believe that I have excessive control over others, often ignoring a balanced perspective.",
                "I hold a belief that life should be fair, which leads to frustration and resentment when things do not turn out as I expect them to.",
                "I insist on the correctness of my viewpoint, disregarding evidence or differing opinions, which prevents me from accepting mistakes or understanding others' perspectives."
            ]
        }

        # Create a DataFrame
        df = pd.DataFrame(distortions_data)
        df.index += 1
        # Display the DataFrame as a table in Streamlit
        st.table(df)
        st.header("Labeling Different Thoughts")
        st.markdown(
            "The statements below are thoughts that can arise to an individual due to encountering different situations in their day to day lives. Read each one of them and label it to the distortion it belongs to.")


        # try:
        #     thoughts_df = pd.read_csv(csv_file, usecols=[0], header=None)
        #     thoughts_list = thoughts_df.iloc[:10, 0] # Select only the first 10 thoughts
        # except Exception as e:
        #     st.error(f"Failed to read CSV file: {e}")
        #     thoughts_list = []
        #
        # if thoughts_list.empty:
        #     st.write("No thoughts available to display.")


        for i, thought in enumerate(st.session_state.user_thoughts, 1):
            st.subheader(f"Thought {i}")
            st.write(thought)
            existing_label_data = st.session_state.responses.get(thought, {"label": "Select a label"})

            # Ensure that existing_label_data is a dictionary; if not, reset it
            if isinstance(existing_label_data, dict):
                existing_label = existing_label_data.get('label', "Select a label")
            else:
                # Reset existing_label_data to ensure dictionary format if it's incorrectly a string
                print(f"Unexpected type for existing_label_data: {type(existing_label_data)}. Resetting to default.")
                existing_label = "Select a label"
                st.session_state.responses[thought] = {"label": existing_label}

            # Prepare the options with a default "Select a label" entry.
            options = ["Select a label"] + distortions_data["Type of Cognitive Distortion"]

            # Only attempt to find the index if the existing label is valid.
            if existing_label in distortions_data["Type of Cognitive Distortion"]:
                default_index = distortions_data["Type of Cognitive Distortion"].index(existing_label) + 1
            else:
                default_index = 0  # Default to "Select a label"

            selected_distortion = st.selectbox(
                "Which Cognitive Distortion does this thought follow?",
                options=options,
                key=f"distortion_{i}",
                index=default_index
            )

            if selected_distortion != "Select a label":
                st.session_state.responses[thought] = {"label": selected_distortion}
                save_response(st.session_state.username, thought, selected_distortion)
                st.write("You selected:", selected_distortion)

        if st.button("Next"):
            if len(st.session_state.user_thoughts) == len(st.session_state.responses):
                if all(value != "Select a label" for value in st.session_state.responses.values()):
                    # response_data = pd.DataFrame(list(st.session_state.responses.items()), columns=['Thought', 'Label'])
                    # response_data.to_csv('labeled_thoughts.csv',mode='w', index=False)
                    # clear_responses(st.session_state.username)  # Clear ongoing responses after submission.
                    st.session_state.responses[thought] = {"label": selected_distortion}
                    save_response(st.session_state.username, thought, selected_distortion)
                    st.session_state.nextsection_done = True
            else:
                st.error("Please label all thoughts before submitting.")

if st.session_state.nextsection_done:
    user_labels = load_user_labels(st.session_state.username)
    gpt_labels = load_gpt_labels()
    st.header("GPT Labeling")
    all_radio_filled = True
    for j, (thought, user_label) in enumerate(user_labels.items(), start=1):
        gpt_label = gpt_labels.get(thought, "No GPT label found")
        st.subheader(f"Thought {j}")
        st.write(f" {thought}")
        st.write(f"**Your Label**: {user_label}")
        st.write(f"**GPT Label**: {gpt_label}")

        previous_agree = st.session_state.responses.get(thought, {}).get('agree')

        # If no session data, load it from CSV
        if previous_agree is None:
            loaded_responses = load_responses(st.session_state.username)
            previous_agree = loaded_responses.get(thought, {}).get('agree')

        # Determine the default index based on previous_agree
        if previous_agree == 1:
            agree_index = 0  # "Yes"
        elif previous_agree == 0:
            agree_index = 1  # "No"
        else:
            agree_index = None

        agree = st.radio(
            f"Do you agree with GPT's label?",
            ["Yes", "No"],
            index=agree_index,
            key=f"agree_{thought}"
        )

        # Save the agreement if selected, and check if all are filled
        if agree:
            st.session_state.gpt_agreements[thought] = 1 if agree == "Yes" else 0
            save_response(st.session_state.username, thought, user_label, 1 if agree == "Yes" else 0)
        else:
            all_radio_filled = False


        # Show submit button only if all radio buttons are filled
    button = st.button("Submit Survey")
    if all_radio_filled:
        if button:
            response_data = pd.DataFrame([
                {'Thought': thought, 'Label': label_data['label']}
                for thought, label_data in st.session_state.responses.items()
            ])
            response_data.to_csv('labeled_thoughts.csv', mode='a', header=False, index=False)
            clear_responses(st.session_state.username)
            update_submission_status(st.session_state.username)
            st.success("Thank you for completing the Mindwell Survey!")
    else:
        st.warning("Please respond to all statements before submitting.")
