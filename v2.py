import streamlit as st
import pandas as pd

thoughts_csv = 'thoughts.csv'
all_thoughts = pd.read_csv(thoughts_csv, header=None).iloc[:, 0].tolist()  # Assuming thoughts are in the first column
thoughts_per_user = 5
assigned_thoughts = 'assigned_thoughts.csv'
ongoing_responses_file = 'responses.csv'
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user1' not in st.session_state:
    st.session_state.user1 = None
if 'user2' not in st.session_state:
    st.session_state.user2 = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'consent_given' not in st.session_state:
    st.session_state.consent_given = False
if 'responses' not in st.session_state:
    st.session_state.responses = {}
if 'start_index' not in st.session_state:
    st.session_state.start_index = None
if 'end_index' not in st.session_state:
    st.session_state.end_index = None
if "other_clicked" not in st.session_state:
    st.session_state.other_clicked = False
if "custom_interest" not in st.session_state:
    st.session_state.custom_interest = None

def load_usernames():
    try:
        df = pd.read_csv('users.csv')
        if 'Username' not in df.columns or 'Password' not in df.columns:
            raise ValueError("CSV file is missing necessary 'Username' or 'Password' columns.")
        return df
    except Exception as e:
        st.error(f"Failed to load users: {e}")
        return pd.DataFrame(columns=['User 1','User 2', 'Password'])
def save_response(username, thought, label1, label2, agree=None):
    # Load existing data if available.
    try:
        responses_df = pd.read_csv(ongoing_responses_file)
    except FileNotFoundError:
        responses_df = pd.DataFrame(columns=['Username', 'Thought', 'Label1', 'Label2', 'Agree'])

    # Update if the thought already exists or append a new one.
    mask = (responses_df['Username'] == username) & (responses_df['Thought'] == thought)
    if responses_df[mask].empty:
        new_row = pd.DataFrame([[username, thought, label1, label2, agree]], columns=['Username', 'Thought', 'Label1', 'Label2', 'Agree'])
        responses_df = pd.concat([responses_df, new_row], ignore_index=True)
    else:
        responses_df.loc[mask, 'Label1'] = label1
        responses_df.loc[mask, 'Label2'] = label2
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
        return {row['Thought']: {'label1': row['Label1'], 'label2' : row['Label2'], 'agree': row['Agree']} for index, row in user_responses.iterrows()}
    except FileNotFoundError:
        return {}

users = load_usernames()
def get_user_thoughts(username):
    assigned_thoughts_df = pd.read_csv(assigned_thoughts)
    user_row = assigned_thoughts_df[(assigned_thoughts_df['User 1'] == username) | (assigned_thoughts_df['User 2'] == username)]
    if not user_row.empty:
        return user_row['Thoughts'].values[0].split('|')
    else:
        return None

def storeage():
    username = st.session_state.username
    age_group = st.session_state.age_group
    users_df = pd.read_csv('users.csv')
    user_index = users_df[users_df['Username'] == username].index
    if not user_index.empty:
        users_df.loc[user_index, 'Age'] = age_group
        users_df.to_csv('users.csv', index=False)
    age_groups = ["21-34", "35-44", "45-55", "55+"]
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

def storeinterest():
    username = st.session_state.username
    field_interest = st.session_state.field_interest
    custom_interest = st.session_state.custom_interest
    st.session_state.other_clicked = st.session_state.field_interest == "Other"

    users_df = pd.read_csv('users.csv')
    user_index = users_df[users_df['Username'] == username].index
    if not user_index.empty:
        users_df.loc[user_index, 'Interest'] = field_interest
        users_df.to_csv('users.csv', index=False)
    field_of_interest = ["Counseling", "Clinical Psychology", "Therapy", "Other"]

    if st.session_state.field_interest == "Other":
        if not user_index.empty:
            users_df.loc[user_index, 'Interest'] = custom_interest
            users_df.to_csv('users.csv', index=False)
        st.session_state.field_interest_index = len(field_of_interest)-1
    else:
        st.session_state.field_interest_index = field_of_interest.index(field_interest)

def update_consent():
    user_response = st.session_state.consent
    if user_response == 'Yes, I give my consent.':
        st.session_state.consent_given = True
    else:
        st.session_state.consent_given = False

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
        age_groups = ["21-34", "35-44", "45-55", "55+"]
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
            print("Here")  # Will show in terminal
            if user_info['Interest'] in fields_of_interest:
                print("Initialized session state")  # Will show in terminal
                st.session_state.field_interest = user_info['Interest']
                st.session_state.field_interest_index = fields_of_interest.index(user_info['Interest'])
            else:
                st.session_state.field_interest = "Other"
                st.session_state.other_clicked = True
                st.session_state.custom_interest = user_info['Interest']
                st.session_state.field_interest_index = len(fields_of_interest) - 1




    else:
        st.error("Invalid username or password. Please try again.")

def update_submission_status(username):
    users_df = pd.read_csv('users.csv')
    user_index = users_df[users_df['Username'] == username].index
    if not user_index.empty:
        users_df.loc[user_index, 'Submitted'] = 1
        users_df.to_csv('users.csv', index=False)

def load_user_labels(username):
    try:
        responses_df = pd.read_csv(ongoing_responses_file)
        user_responses = responses_df[responses_df['Username'] == username]
        return dict(zip(user_responses['Thought'], user_responses['Label1'], user_responses['Label2']))
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
        st.button('Login',on_click=login, args=(username_input, password_input), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.logged_in:
    if not st.session_state.consent_given:
        st.header("Mindwell Survey")
        st.subheader("MindWell is a project dedicated to gathering data on several types of cognitive distortions. We’re harnessing the power of artificial intelligence to detect and classify cognitive distortions from written text. Your participation is crucial in building a diverse dataset that will not only serve the community but also facilitate the development of applications designed to enhance awareness of cognitive distortions.")
        st.write("This survey will take less than 10 minutes to complete.")

        consent = st.radio(
            "By clicking yes, you agree that you have read and understood the information included in this form, agree to participate in this study and that you are above 18 years of age.",
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
        default_interest = st.session_state.get('field_interest_index', None)
        place_holder_default = st.session_state.get('custom_interest', "Enter your area of expertise")
        age_group = st.radio(
            "Select your age group:",
            ["21-34", "35-44", "45-55", "55+"],
            key='age_group', index=default_age_index,
            on_change=storeage
        )
        # years = st.slider("Years of Experience", 1, 30)
        years_of_experience = st.radio(
            "Select how many years you have been dealing with patients:",
            ["Below a year", "1-3 years", "4-7 years", "8-11 years", "12+ years"],
            key='years_of_experience', index=default_experience_index,
            on_change=storeyear
        )
        # field_of_interest = st.radio(
        #     "Select your area of expertise:",
        #     ["Counseling", "Clinical Psychology", "Therapy", "Other"],
        #     key='field_interest', index=default_interest,
        #     on_change=storeinterest
        # )
        # if st.session_state.other_clicked:
        #         st.text_input(
        #             "Please specify your area of expertise:",
        #             key="custom_interest",
        #             placeholder=place_holder_default,
        #             on_change=storeinterest
        #         )

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
            existing_label1_data = st.session_state.responses.get(thought, {"label1": "Select a label1"})
            existing_label2_data = st.session_state.responses.get(thought, {"label2": "Select a label2 or Same label if no other label"})
            if isinstance(existing_label1_data, dict):
                existing_label1 = existing_label1_data.get('label1', "Select a label1")
            else:
                # Reset existing_label_data to ensure dictionary format if it's incorrectly a string
                print(f"Unexpected type for existing_label_data: {type(existing_label1_data)}. Resetting to default.")
                existing_label1 = "Select a label1"
                st.session_state.responses[thought] = {"label1": existing_label1}

            if isinstance(existing_label2_data, dict):
                existing_label2 = existing_label2_data.get('label2', "Select a label2 or Same label if no other label")
            else:
                # Reset existing_label_data to ensure dictionary format if it's incorrectly a string
                print(f"Unexpected type for existing_label_data: {type(existing_label2_data)}. Resetting to default.")
                existing_label2 = "Select a label2 or Same label if no other label"
                st.session_state.responses[thought] = {"label2": existing_label2}

            # Prepare the options with a default "Select a label" entry.
            options1 = ["Select a label1"] + distortions_data["Type of Cognitive Distortion"]
            options2 = ["Select a label2 or Same label if no other label"] + distortions_data["Type of Cognitive Distortion"]

            # Only attempt to find the index if the existing label is valid.
            if existing_label1 in distortions_data["Type of Cognitive Distortion"]:
                default_index_1 = distortions_data["Type of Cognitive Distortion"].index(existing_label1) + 1
            else:
                default_index_1 = 0  # Default to "Select a label"

            if existing_label2 in distortions_data["Type of Cognitive Distortion"]:
                default_index_2 = distortions_data["Type of Cognitive Distortion"].index(existing_label2) + 1
            else:
                default_index_2 = 0  # Default to "Select a label"

            selected_distortion_1 = st.selectbox(
                "Which Cognitive Distortion does this thought follow?",
                options=options1,
                key=f"distortion_1_{i}",
                index=default_index_1
            )

            selected_distortion_2 = st.selectbox(
                "Which Cognitive Distortion does this thought follow?",
                options=options2,
                key=f"distortion_2_{i}",
                index=default_index_2
            )

            # if selected_distortion_1 != "Select a label1":
            #     st.session_state.responses[thought] = {"label1": selected_distortion_1}
            #     if selected_distortion_2 != "Select a label2 or Same label if no other label":
            #         st.session_state.responses[thought] = {"label2": selected_distortion_2}

            if selected_distortion_1 != "Select a label1":
                st.session_state.responses[thought] = st.session_state.responses.get(thought, {})
                st.session_state.responses[thought]["label1"] = selected_distortion_1

            if selected_distortion_2 != "Select a label2 or Same label if no other label":
                st.session_state.responses[thought] = st.session_state.responses.get(thought, {})
                st.session_state.responses[thought]["label2"] = selected_distortion_2

            save_response(st.session_state.username, thought, selected_distortion_1, selected_distortion_2)
            st.write("You selected label1 :", selected_distortion_1)
            st.write("You selected label2 :", selected_distortion_2)



        # Check if all responses are completed and valid
        is_ready_to_submit = (
                len(st.session_state.user_thoughts) == len(st.session_state.responses) and
                all(value != "Select a label1" or value != "Select a label2 or Same label if no other label" for value in st.session_state.responses.values())
        )


        # Submit button (disabled if responses are incomplete)
        button = st.button("Submit Survey", disabled=not is_ready_to_submit)

        if button:
            # Ensure all thoughts are labeled
            if len(st.session_state.user_thoughts) == len(st.session_state.responses):
                if all(value != "Select a label1" or value != "Select a label2 or Same label if no other label" for value in st.session_state.responses.values()):
                    # Save current responses
                    for thought in st.session_state.user_thoughts:
                        if thought not in st.session_state.responses:
                            st.session_state.responses[thought] = {
                                "label1": selected_distortion_1,
                                "label2": selected_distortion_2
                            }
                            save_response(st.session_state.username, thought, selected_distortion_1,selected_distortion_2)

                    # Prepare DataFrame and save to CSV
                    response_data = pd.DataFrame([
                        {'Thought': thought, 'Label1': label_data['label1'], 'Label2': label_data['label2']}
                        for thought, label_data in st.session_state.responses.items()
                    ])
                    response_data.to_csv('labeled_thoughts.csv', mode='a', header=False, index=False)

                    # Clear session state responses and update submission status
                    clear_responses(st.session_state.username)
                    update_submission_status(st.session_state.username)

                    # Success message
                    st.session_state.survey_submitted = True
                    st.success("Thank you for completing the Mindwell Survey!")
                else:
                    st.error("Please label all thoughts before submitting.")
            else:
                st.error("Please label all thoughts before submitting.")

        # Display a warning if the button is disabled
        if not is_ready_to_submit:
            st.warning("Please respond to all statements and select a label for each before submitting.")
