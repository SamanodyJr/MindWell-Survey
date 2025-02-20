import streamlit as st
import pandas as pd
from pymongo import MongoClient

# ----------------------------------------------------------------
# 1) MONGODB CONNECTION (Update with your actual credentials)
# ----------------------------------------------------------------
MONGO_URI = "mongodb+srv://mindwell:mindwell@testingforinternship.swtanol.mongodb.net/?retryWrites=true&w=majority&appName=testingForInternship"
mongo_client = MongoClient(MONGO_URI)

# Database
mongo_db = mongo_client["mindwell_survey_db"]

# Collections
users_collection = mongo_db["users"]                 # Replaces users.csv
responses_collection = mongo_db["ongoing_responses"] # For partial responses
final_labels_collection = mongo_db["final_labeled_thoughts"] # For final labels

# ----------------------------------------------------------------
# 2) REPLACE users.csv FUNCTIONS WITH MONGODB QUERIES
# ----------------------------------------------------------------
def get_user_record(username: str):
    """
    Return a dict with the user's record from MongoDB, or None if not found.
    Example fields:
      - Username
      - Password
      - Submitted
      - Age
      - Experience
      - Interest
    """
    return users_collection.find_one({"Username": username})

def check_password(username: str, password: str) -> bool:
    """
    Return True if the user exists and password matches, else False.
    """
    doc = get_user_record(username)
    if not doc:
        return False
    return doc.get("Password", "") == password

def user_already_submitted(username: str) -> bool:
    """
    Return True if 'Submitted' field is 1 (or True) in DB, else False.
    """
    doc = get_user_record(username)
    if not doc:
        return False
    return doc.get("Submitted", 0) == 1

def update_submission_status(username: str):
    """
    Mark 'Submitted' = 1 for the given user in DB.
    """
    users_collection.update_one(
        {"Username": username},
        {"$set": {"Submitted": 1}}
    )

def store_age(username: str, age_group: str):
    """
    Update the 'Age' field for the given user in DB.
    """
    users_collection.update_one(
        {"Username": username},
        {"$set": {"Age": age_group}}
    )

def store_experience(username: str, years_of_experience: str):
    """
    Update the 'Experience' field for the given user in DB.
    """
    users_collection.update_one(
        {"Username": username},
        {"$set": {"Experience": years_of_experience}}
    )

def store_interest(username: str, interest: str):
    """
    Update the 'Interest' field for the given user in DB.
    """
    users_collection.update_one(
        {"Username": username},
        {"$set": {"Interest": interest}}
    )

# ----------------------------------------------------------------
# 3) PARTIAL AND FINAL RESPONSES (Same as you had before w/ Mongo)
# ----------------------------------------------------------------
def save_response(username, thought, label1, label2, agree=None):
    query = {"Username": username, "Thought": thought}
    update = {
        "$set": {
            "Username": username,
            "Thought": thought,
            "Label1": label1,
            "Label2": label2,
            "Agree": agree
        }
    }
    responses_collection.update_one(query, update, upsert=True)

def load_responses(username):
    user_docs = list(responses_collection.find({"Username": username}))
    user_responses = {}
    for doc in user_docs:
        user_responses[doc["Thought"]] = {
            "label1": doc.get("Label1", "Select the Cognitive Distortion"),
            "label2": doc.get("Label2", "Select another Cognitive Distortion or None"),
            "agree": doc.get("Agree", None)
        }
    return user_responses

def clear_responses(username):
    responses_collection.delete_many({"Username": username})

def save_final_label(thought, label1, label2):
    final_labels_collection.insert_one({
        "Thought": thought,
        "Label1": label1,
        "Label2": label2
    })

# ----------------------------------------------------------------
# 4) REMAINING GLOBALS (thoughts.csv, assigned_thoughts.csv, etc.)
# ----------------------------------------------------------------
thoughts_csv = 'thoughts.csv'
assigned_thoughts = 'assigned_thoughts.csv'

all_thoughts = pd.read_csv(thoughts_csv, header=None).iloc[:, 0].tolist()  # first column
thoughts_per_user = 5

# We'll no longer reference users.csv anywhere.

# -- Session state initialization --
if 'username' not in st.session_state:
    st.session_state.username = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'consent_given' not in st.session_state:
    st.session_state.consent_given = False
if 'responses' not in st.session_state:
    st.session_state.responses = {}
if 'survey_submitted' not in st.session_state:
    st.session_state.survey_submitted = False

# We'll keep these for advanced usage
if 'user1' not in st.session_state:
    st.session_state.user1 = None
if 'user2' not in st.session_state:
    st.session_state.user2 = None
if 'start_index' not in st.session_state:
    st.session_state.start_index = None
if 'end_index' not in st.session_state:
    st.session_state.end_index = None
if "other_clicked" not in st.session_state:
    st.session_state.other_clicked = False
if "custom_interest" not in st.session_state:
    st.session_state.custom_interest = None

# ----------------------------------------------------------------
# 5) Retrieve assigned thoughts from assigned_thoughts.csv
# ----------------------------------------------------------------
def get_user_thoughts(username):
    assigned_thoughts_df = pd.read_csv(assigned_thoughts)
    user_row = assigned_thoughts_df[
        (assigned_thoughts_df['User 1'] == username) |
        (assigned_thoughts_df['User 2'] == username)
    ]
    if not user_row.empty:
        return user_row['Thoughts'].values[0].split('|')
    else:
        return []

# ----------------------------------------------------------------
# 6) Login function (uses MongoDB instead of users.csv)
# ----------------------------------------------------------------
def login(username_input, password_input):
    # Check password
    if not check_password(username_input, password_input):
        st.error("Invalid username or password. Please try again.")
        return

    # If user has already submitted
    if user_already_submitted(username_input):
        st.session_state.logged_in = True
        st.session_state.username = username_input
        st.session_state.survey_submitted = True
        st.success("Thank you! You have already completed the survey.")
        st.stop()
    else:
        # Not submitted yet
        st.session_state.logged_in = True
        st.session_state.username = username_input
        # Load assigned thoughts
        st.session_state.user_thoughts = get_user_thoughts(username_input)
        # Load partial responses from DB
        st.session_state.responses = load_responses(username_input)
        st.success(f"Welcome to our survey, {username_input}!")

        # Attempt to restore user info from DB
        doc = get_user_record(username_input)
        if doc:
            # For example, if doc["Age"] is set, store it in st.session_state
            # We'll define lists for indexes
            age_groups = ["21-34", "35-44", "45-55", "55+"]
            exp_levels = ["Below a year", "1-3 years", "4-7 years", "8-11 years", "12+ years"]
            field_of_interest = ["Counseling", "Clinical Psychology", "Therapy", "Other"]

            # Age
            if doc.get("Age") in age_groups:
                st.session_state.age_group = doc["Age"]
                st.session_state.age_group_index = age_groups.index(doc["Age"])

            # Experience
            if doc.get("Experience") in exp_levels:
                st.session_state.years_of_experience = doc["Experience"]
                st.session_state.years_of_experience_index = exp_levels.index(doc["Experience"])

            # Interest
            if doc.get("Interest") in field_of_interest:
                st.session_state.field_interest = doc["Interest"]
                st.session_state.field_interest_index = field_of_interest.index(doc["Interest"])
            elif doc.get("Interest"):
                # Something not in the list => treat it as "Other"
                st.session_state.field_interest = "Other"
                st.session_state.other_clicked = True
                st.session_state.custom_interest = doc["Interest"]
                st.session_state.field_interest_index = len(field_of_interest) - 1

# ----------------------------------------------------------------
# 7) Utility for storing user data (Age, Experience, etc.)
#    but now in MongoDB instead of CSV
# ----------------------------------------------------------------
def storeage():
    username = st.session_state.username
    age_group = st.session_state.age_group
    store_age(username, age_group)
    age_groups = ["21-34", "35-44", "45-55", "55+"]
    st.session_state.age_group_index = age_groups.index(age_group)

def storeyear():
    username = st.session_state.username
    years_of_experience = st.session_state.years_of_experience
    store_experience(username, years_of_experience)
    exp_levels = ["Below a year", "1-3 years", "4-7 years", "8-11 years", "12+ years"]
    st.session_state.years_of_experience_index = exp_levels.index(years_of_experience)

def storeinterest():
    username = st.session_state.username
    field_interest = st.session_state.field_interest
    custom_interest = st.session_state.custom_interest

    st.session_state.other_clicked = (field_interest == "Other")

    if field_interest == "Other" and custom_interest:
        # Save the custom interest
        store_interest(username, custom_interest)
    else:
        # Save the chosen interest
        store_interest(username, field_interest)

def update_consent():
    user_response = st.session_state.consent
    st.session_state.consent_given = (user_response == 'Yes, I give my consent.')

# ----------------------------------------------------------------
# 8) MAIN STREAMLIT LOGIC
# ----------------------------------------------------------------

# If user already submitted, skip everything
if st.session_state.survey_submitted:
    st.success("Thank you for completing the Mindwell Survey!")
    st.stop()

# If not logged in, show login
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center; color: grey;'>Mindwell Survey</h2>", unsafe_allow_html=True)

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
        st.button('Login', on_click=login, args=(username_input, password_input), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()  # No further UI if not logged in

# -- If logged in, handle consent if not given yet
if not st.session_state.consent_given:
    st.header("Mindwell Survey")
    st.subheader(
        "MindWell is a project dedicated to gathering data on several types of cognitive distortions. "
        "We’re harnessing the power of artificial intelligence to detect and classify cognitive distortions "
        "from written text. Your participation is crucial in building a diverse dataset..."
    )
    st.write("This survey will take less than 10 minutes...")

    st.radio(
        "By clicking yes, you agree...",
        ('Yes, I give my consent.', 'No, I do not give my consent.'),
        index=None,
        on_change=update_consent,
        key='consent'
    )

# If user consented, show the main form
if st.session_state.consent_given:
    st.write("Thank you for your consent.")
    st.markdown("## Survey Questions")

    # Attempt to set default indexes
    default_age_index = st.session_state.get('age_group_index', None)
    default_experience_index = st.session_state.get('years_of_experience_index', None)
    default_interest_index = st.session_state.get('field_interest_index', None)
    place_holder_default = st.session_state.get('custom_interest', "Enter your area of expertise")

    # Age group
    st.radio(
        "Select your age group:",
        ["21-34", "35-44", "45-55", "55+"],
        key='age_group',
        index=default_age_index,
        on_change=storeage
    )

    # Years of experience
    st.radio(
        "Select how many years you have been dealing with patients:",
        ["Below a year", "1-3 years", "4-7 years", "8-11 years", "12+ years"],
        key='years_of_experience',
        index=default_experience_index,
        on_change=storeyear
    )

    # If you want to ask for area of expertise (commented out by default)
    # st.radio(
    #     "Select your area of expertise:",
    #     ["Counseling", "Clinical Psychology", "Therapy", "Other"],
    #     key='field_interest',
    #     index=default_interest_index,
    #     on_change=storeinterest
    # )
    # if st.session_state.other_clicked:
    #     st.text_input(
    #         "Please specify your area of expertise:",
    #         key="custom_interest",
    #         placeholder=place_holder_default,
    #         on_change=storeinterest
    #     )

    # Distortions Table
    st.header("Cognitive Distortions")
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
            "I view a situation... on a continuum.",
            "I predict the future... that I will not be able to stand it.",
            "I believe my emotions reflect reality...",
            "I put a fixed, global label...",
            "I pay attention to one or a few details...",
            "I believe that I know the thoughts or intentions of others...",
            "I take isolated negative cases and generalize them...",
            "I assume that others' behaviors are directed at me...",
            "I tell myself that events... should be the way I expected...",
            "I direct my attention to others as sources of my negative feelings...",
            "I disqualify positive experiences or events...",
            "I feel that I am either externally controlled...",
            "I hold a belief that life should be fair...",
            "I insist on the correctness of my viewpoint..."
        ]
    }
    df = pd.DataFrame(distortions_data)
    df.index += 1
    st.table(df)

    st.header("Labeling Different Thoughts")
    st.markdown("Read each thought below and label it...")

    # Show each assigned thought
    for i, thought in enumerate(st.session_state.user_thoughts, 1):
        st.subheader(f"Thought {i}")
        st.write(thought)

        existing_response = st.session_state.responses.get(thought, {})
        existing_label1 = existing_response.get("label1", "Select the Cognitive Distortion")
        existing_label2 = existing_response.get("label2", "Select another Cognitive Distortion or None")

        options1 = ["Select the Cognitive Distortion"] + distortions_data["Type of Cognitive Distortion"] + ["None"]
        options2 = ["Select another Cognitive Distortion or None"] + distortions_data["Type of Cognitive Distortion"] + ["None"]

        default_index_1 = options1.index(existing_label1) if existing_label1 in options1 else 0
        default_index_2 = options2.index(existing_label2) if existing_label2 in options2 else 0

        selected_distortion_1 = st.selectbox(
            "Which Cognitive Distortion (Primary)?",
            options=options1,
            key=f"distortion_1_{i}",
            index=default_index_1
        )

        selected_distortion_2 = st.selectbox(
            "Which Cognitive Distortion (Secondary)?",
            options=options2,
            key=f"distortion_2_{i}",
            index=default_index_2
        )

        # Store in session + Save partial to DB
        st.session_state.responses[thought] = {
            "label1": selected_distortion_1,
            "label2": selected_distortion_2
        }

        save_response(
            st.session_state.username,
            thought,
            selected_distortion_1,
            selected_distortion_2
        )

        st.write("Primary label:", selected_distortion_1)
        st.write("Secondary label:", selected_distortion_2)

    # Final Submit
    is_ready_to_submit = (
        len(st.session_state.user_thoughts) == len(st.session_state.responses) and
        all(
            (resp.get("label1") not in ["Select another Cognitive Distortion"]) and
            (resp.get("label2") not in ["Select another Cognitive Distortion or None"])
            for resp in st.session_state.responses.values()
        )
    )

    if st.button("Submit Survey", disabled=not is_ready_to_submit):
        if len(st.session_state.user_thoughts) == len(st.session_state.responses):
            all_labeled = all(
                (resp.get("label1") not in ["Select another Cognitive Distortion"]) and
                (resp.get("label2") not in ["Select another Cognitive Distortion or None"])
                for resp in st.session_state.responses.values()
            )
            if all_labeled:
                # Save final labeled thoughts to DB
                for thought in st.session_state.user_thoughts:
                    label1 = st.session_state.responses[thought].get("label1", "")
                    label2 = st.session_state.responses[thought].get("label2", "")
                    save_final_label(thought, label1, label2)

                # Clear partial responses
                clear_responses(st.session_state.username)

                # Mark user as submitted
                update_submission_status(st.session_state.username)

                st.session_state.survey_submitted = True
                st.rerun()
            else:
                st.error("Please label all thoughts with both labels before submitting.")
        else:
            st.error("Please label all thoughts before submitting.")

    if not is_ready_to_submit:
        st.warning("Provide both labels for ALL thoughts before submitting.")
