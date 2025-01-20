import streamlit as st
import requests
import logging
from streamlit.components.v1 import html
from datetime import datetime, timedelta
# from streamlit_autorefresh import st_autorefresh
# import login_decorator
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Backend API URL
BACKEND_URL = "http://127.0.0.1:8000"
# job_names_history = {}
SESSION_EXPIRATION = timedelta(minutes=30)

FRONTEND_URL = "http://localhost:8501"


def copy_to_clipboard(text, key):
    return html(f"""
        <button onclick="navigator.clipboard.writeText(document.getElementById('text_{key}').value)">Copy</button>
        <textarea id="text_{key}" style="display:none;">{text}</textarea>
    """, height=30)


# CSS for styling the custom button
button_style = """
    <style>
        .custom-button {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 15px 32px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 4px;
        }
    </style>
"""




# decorator

# decorator
def ensure_authenticated(func):
    def wrapper(*args, **kwargs):
        token = st.session_state.get("token")
        expiration_time = st.session_state.get("expiration_time")
        if token and expiration_time and datetime.now() < expiration_time:
            return func(*args, **kwargs)
        else:
            st.warning("Session expired or not logged in. Please login again.")
            login()

    return wrapper


def register():
    st.title("Register")
    with st.form(key='register_form'):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        is_active = st.checkbox("Is Active", value=True)
        is_superuser = st.checkbox("Is Superuser", value=False)
        is_verified = st.checkbox("Is Verified", value=False)
        submit_button = st.form_submit_button(label='Register')

    if submit_button:
        if password != confirm_password:
            st.error("Passwords do not match")
        else:
            payload = {
                "email": email,
                "password": password,
                "is_active": is_active,
                "is_superuser": is_superuser,
                "is_verified": is_verified
            }
            try:
                response = requests.post(f"{BACKEND_URL}/auth/register", json=payload)
                response.raise_for_status()
                if response.status_code == 201:
                    st.success("Registered successfully")
                else:
                    st.error(response.json().get("detail", "Registration failed"))
            except requests.exceptions.RequestException as e:
                logger.error(f"Registration error: {e}")
                st.error("Failed to register. Please try again later.")


def login():
    st.title("Login")
    with st.form(key='login_form'):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button(label='Login')

    if submit_button:
        try:
            response = requests.post(f"{BACKEND_URL}/auth/jwt/login", data={"username": email, "password": password})
            response.raise_for_status()
            if response.status_code == 200:
                token = response.json().get("access_token")
                expiration_time = datetime.now() + timedelta(hours=1)
                st.session_state["token"] = token
                # requests.session["token"] = token
                # print(requests.session.get("token"),"server session")
                st.session_state["authenticated"] = True
                st.success("Logged in successfully")
                st.session_state["expiration_time"] = expiration_time
                st.experimental_set_query_params(page="create", token=token)
                st.rerun()
            else:
                st.error("Invalid email or password")
        except requests.exceptions.RequestException as e:
            logger.error(f"Login error: {e}")
            st.error("Failed to login. Please try again later.")


def logout():
    st.session_state.pop("token", None)
    st.session_state.pop("expiration_time", None)
    st.session_state.pop("authenticated", None)
    st.success("Logged out successfully")
    st.rerun()


@ensure_authenticated
def beautify_job_description(token, job_data):
    # global job_names_history  # Accessing Global history

    st.title("Beautified Job Description")

    role_options = ["Python Developer", "Senior Accountant", "Machine Learning Engineer",
                    "Senior Cloud Platform Engineer",
                    "Java Developer", "Ruby Developer", "SAP", "ReactJs", "Frontend Developer", "Backend Developer",
                    "Fullstack Developer", "Accountant", "Scrum Master", "BI", "BA", "Manager", "Scrum Manager"]
    experience_options = ["0-2 years", "2-4 years", "5-8 years", "10-15 years"]
    location_options = ["Chennai", "Bangalore", "PAN India", "Trichy", "Madurai", "Coimbatore", "Hyderabad",
                        "Trivandrum"]

    role, experience, location = st.columns(3)
    with role:
        # role_input = st.selectbox("Select Role", role_options, index=0)
        role_input = st.text_input("Enter the role", value=job_data.get('role', ''))

    with experience:
        experience_input = st.selectbox("Select Experience", experience_options,
                                        index=experience_options.index(job_data.get('experience', '0-2 years')))

    with location:
        # location_input = st.selectbox("Select Location", location_options, index=0)
        location_input = st.text_input("Enter the Location", value=job_data.get('location', ''))

    job_description = st.text_area("Enter Job Description", value=job_data.get('job_description', ''), height=100)

    if st.button("Beautify"):
        # valid the inputs

        if not role_input:
            st.warning("Please enter a valid role")
        elif experience_input == "Select Experience":
            st.warning("Please Select a Valid experience level")
        elif not location_input.strip():
            st.warning("Please enter a valid location")
        elif not isinstance(job_description, str) or not job_description.strip():
            st.warning("Job Description should be a valid non-empty  string")
        elif job_description.strip():
            try:
                response = requests.post(f"{BACKEND_URL}/beautify_job_description",
                                         json={"job_description": job_description,
                                               "role": role_input,
                                               "experience": experience_input,
                                               "location": location_input},
                                         headers={"Authorization": f"Bearer {token}"})
                response.raise_for_status()

                data = response.json()
                # beautified_job_description = data["beautified_job_description"]
                beautified_job_description = data.get("beautified_job_description", [])
                if not beautified_job_description:
                    st.error("No beautified job descriptions found.")

                else:
                    for i, description in enumerate(beautified_job_description):
                        st.text_area(f"Beautified Job Description {i + 1}", description,
                                     key=f"beautified_job_description_{i + 1}", height=600)
                        copy_to_clipboard(description, i)

                    # if user_id not in job_names_history:
                    #     job_names_history[user_id] = []
                    #     job_names_history[user_id].extend([role_input] * len(beautified_job_description))

            except requests.exceptions.RequestException as e:
                st.error(f"Error: {e}")

        else:
            # Display inputs if all validations pass
            st.write("Role:", role_input)
            st.write("Experience:", experience_input)
            st.write("Location:", location_input)
            st.write("Job Description:", job_description)


# job description history

def get_job_description_history(token):
    try:
        response = requests.get(f"{BACKEND_URL}/job_description_history",
                                headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch job description history: {e}")
        return []


def display_beautified_descriptions(job):
    st.title("Beautified Job Descriptions")
    st.write(f"**Role:** {job['role']}")
    st.write(f"**Experience:** {job['experience']}")
    st.write(f"**Location:** {job['location']}")
    st.write(f"**Job Description:**\n{job['job_description']}")
    st.write(f"**Beautified Description 1:**\n{job['beautified_description_1']}")
    st.write(f"**Beautified Description 2:**\n{job['beautified_description_2']}")
    st.write(f"**Beautified Description 3:**\n{job['beautified_description_3']}")


def delete_job_description(job_id: int):
    try:
        response = requests.delete(f"{BACKEND_URL}/job_description/{job_id}")
        response.raise_for_status()
        st.success("Job description deleted successfully.")
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to delete job description: {e}")


def rename_job_description(job_id: int, new_name: str):
    try:
        response = requests.put(f"{BACKEND_URL}/job_description/{job_id}/rename", json={"new_name": new_name})
        response.raise_for_status()
        st.success("Job description renamed successfully.")
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to rename job description: {e}")


def display_job_descriptions(jobs, heading):
    from urllib.parse import urlencode
    if jobs:
        st.sidebar.markdown(f"### {heading}")
        for idx, job in enumerate(jobs):
            if st.session_state.get("authenticated", True):
                token = st.session_state["token"]
                token_param = urlencode({"token": token})
                job_display = f"{job['role']}"
                job_link = f"{FRONTEND_URL}/?page=beautify&job_id={job['id']}&{token_param}"

                st.sidebar.markdown(
                    f"""
                    <style>
                    .link-style a {{
                        text-decoration: inherit !important;
                        color: #000 !important;
                        padding: .5rem !important;
                        font-size: .875rem !important;
                        line-height:1.25rem !important;
                        height: 35px;
                        align-items: center;
                        display: flex;
                    }}
                    .link-style:hover a {{
                      background-color: #dcdcdc;
                      border-radius: 7px;
                    }}

                    </style>
                    <div class="link-style">
                        <a href="{job_link}" target="_blank">{job_display}</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # st.sidebar.markdown(f'<a href="{job_link}" style="text-decoration:inherit !important;" target="_blank">{job_display}</a>', unsafe_allow_html=True)
    else:
        pass


def main():

    # count = st_autorefresh(interval=60000, limit=100, key="fizzbuzzcounter")
    query_params = st.experimental_get_query_params()
    token_from_url = query_params.get("token", [None])[0]
    page = query_params.get("page", [None])[0]
    job_id = query_params.get("job_id", [None])[0]

    if "token" not in st.session_state:
        st.session_state["token"] = token_from_url
    if "expiration_time" not in st.session_state:
        st.session_state["expiration_time"] = datetime.now() + timedelta(hours=1) if token_from_url else None
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = bool(token_from_url)

    if not st.session_state.get("authenticated"):
        st.sidebar.title("Menu")
        choice = st.sidebar.selectbox("Choose Action", ["Login", "Register"])
        if choice == "Login":
            login()
        elif choice == "Register":
            register()
    else:
        handle_authenticated_user(page, job_id)


def handle_authenticated_user(page, job_id):
    expiration_time = st.session_state["expiration_time"]
    if expiration_time is None or datetime.now() > expiration_time:
        logout()
    else:
        st.sidebar.title("Menu")
        token = st.session_state["token"]

        if st.sidebar.button("Create New Job Description"):
            st.experimental_set_query_params(page="create", token=token)

        job_descriptions = get_job_description_history(token)
        display_job_history(job_descriptions)

        placeholder = st.empty()
        with placeholder.container():
            st.markdown("""
            <style>
              .sidebar-btn-container {
                display: flex;
                justify-content: flex-end;
              }
            </style>
            """, unsafe_allow_html=True)
            st.markdown('<div class="sidebar-btn-container">', unsafe_allow_html=True)
            if st.button("Logout"):
                logout()
                st.session_state["authenticated"] = False
                st.experimental_rerun()

        handle_page_navigation(page, job_id, job_descriptions)


def display_job_history(job_descriptions):
    if job_descriptions:
        for job in job_descriptions:
            if 'created_at' not in job:
                job['created_at'] = datetime.now().isoformat()
        job_descriptions.sort(key=lambda x: x['created_at'], reverse=True)
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        seven_days_ago = today - timedelta(days=7)
        thirty_days_ago = today - timedelta(days=30)

        today_jobs = []
        yesterday_jobs = []
        previous_jobs = []
        last_seven_days_jobs = []
        last_thirty_days_jobs = []
        older_jobs_by_month = {}

        for job in job_descriptions:
            job_date = datetime.fromisoformat(job['created_at']).date()
            if job_date == today:
                today_jobs.append(job)
            elif job_date == yesterday:
                yesterday_jobs.append(job)
            elif seven_days_ago < job_date < yesterday:
                last_seven_days_jobs.append(job)
            elif thirty_days_ago < job_date <= seven_days_ago:
                last_thirty_days_jobs.append(job)
            else:
                month_year = job_date.strftime("%B %Y")
                if month_year not in older_jobs_by_month:
                    older_jobs_by_month[month_year] = []
                older_jobs_by_month[month_year].append(job)

        display_job_descriptions(today_jobs, "Today")
        display_job_descriptions(yesterday_jobs, "Yesterday")
        display_job_descriptions(previous_jobs, "Last 7 Days")
        display_job_descriptions(last_thirty_days_jobs, "Last 30 Days")

        for month_year, jobs in older_jobs_by_month.items():
            display_job_descriptions(jobs, month_year)

    else:
        st.warning("No job descriptions found.")


def handle_page_navigation(page, job_id, job_descriptions):
    if page == "beautify" and job_id:
        selected_job = next((job for job in job_descriptions if str(job["id"]) == job_id), None)
        if selected_job:
            beautify_job_description(st.session_state["token"], selected_job)
            display_beautified_descriptions(selected_job)
        else:
            st.error("Job description not found.")
    elif page == "create":
        beautify_job_description(st.session_state["token"], {})
    else:
        load_user_data(st.session_state["token"])


def load_user_data(token):
    with st.spinner("Loading..."):
        try:
            response = requests.get(f"{BACKEND_URL}/users/me", headers={"Authorization": f"Bearer {token}"})
            response.raise_for_status()
            user_data = response.json()
            user_name = user_data["email"].split("@")[0]
            st.markdown(f"<h2 style='color: green; text-align: right;'>Welcome {user_name}!</h2>",
                        unsafe_allow_html=True)
            beautify_job_description(token, {})
        except requests.exceptions.RequestException as e:
            st.error("Failed to load user data. Please try again later.")


if __name__ == "__main__":
    main()




