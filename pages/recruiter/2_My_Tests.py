import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from st_pages import show_pages, Page, hide_pages

import pandas as pd

from google.cloud.firestore_v1.base_query import FieldFilter

from utils.db import db
from utils.init import initialize_app
from utils.components import sidebar_logout, hide_seperator_from_sidebar
from utils.storage import get_video_url_from_firebase


def my_tests():
    # Page Config
    st.set_page_config(
        page_title="My Tests | Neuradev Coding Test Platform",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Show/Hide Pages on Sidebar
    show_pages([
        Page(path='Home.py'),
        Page(path='pages/recruiter/1_Create_New_Test.py'),
        Page(path='pages/recruiter/2_My_Tests.py'),
    ])
    hide_pages(["candidate"])
    
    # Hide seperator on Sidebar
    hide_seperator_from_sidebar()
    
    # Add Logout button to sidebar
    sidebar_logout()
    
    # Main Section
    st.header("My Tests")
    
    my_tests = db.collection("tests").where(
        filter=FieldFilter("creator", "==", st.session_state.user["email"])).get() 

    if len(my_tests) == 0:
        st.subheader("😔 Oops! No test created")
    else:
        tabs = st.tabs([test.id for test in my_tests])
        for i, tab in enumerate(tabs):
            test = my_tests[i]
            with tab:
                with st.container(border=True):
                    st.write(f"Topic: {test.get('topic')} | Total {len(test.get('problems'))} problems | Time limit: {test.get('time_limit')} mins")
                    st.write(f"Created by {test.get('creator')} at {test.get('created_at').strftime('%Y-%m-%d %H:%M:%S')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader('Problems')
                    problems = test.get("problems")
                    data_df = pd.DataFrame(
                        {
                            "No": [i+1 for i, problem in enumerate(problems)],
                            "Category": [problem["category"] for problem in problems],
                            "Time Limit": [f"{problem['time_limit']} mins" for problem in problems],
                            "Title": [problem["title"] for problem in problems],
                            "Description": [problem["description"] for problem in problems],
                        }
                    )
                    st.dataframe(data_df, hide_index=True)
                with col2:
                    st.subheader('Participants')
                    participants = list(test.to_dict()['participants'].values())
                    participants = [participant for participant in participants if participant["finished_at"]]

                    if len(participants) == 0:
                        st.write("No participant yet")
                    else:
                        for j, participant in enumerate(participants):
                            total_problems = len(test.get('problems'))
                            with st.expander(f"{participant['user']['first_name']} {participant['user']['last_name']} ({'Finished' if participant['finished_at'] else 'In progress'})"):
                                if participant["finished_at"]:
                                    with st.container(border=True):
                                        st.write(f"Passed: {len([solution for solution in participant['solutions'] if solution['passed']])}/{total_problems}")
                                        st.write(f"Overall rating: {round(participant['overall_rating'], 1)}/5")
                                        st.write(f"Overall code quality: {round(participant['overall_code_quality'], 1)}/5")
                                        st.write(f"Overall explanation rating: {round(participant['overall_explanation_rating'], 1)}/5")
                                        st.write(f"Finished at {participant['finished_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                                if total_problems > 0:
                                    problem_tabs = st.tabs([f"Problem {k + 1}" for k, problem in enumerate(test.get('problems'))])
                                    for k, problem_tab in enumerate(problem_tabs):
                                        with problem_tab:
                                            if k >= len(participant['solutions']):
                                                st.write("No solution submitted")
                                            else:
                                                solution = participant['solutions'][k]
                                                with st.container(border=True):
                                                    st.markdown("#### Candidate solution")
                                                    st.code(solution["code"])
                                                    st.write(solution["explanation"])
                                                if solution['passed']:
                                                    st.success('Result: Passed')
                                                else:
                                                    st.error('Result: Failed')
                                                with st.container(border=True):
                                                    st.write(f"Overall rating: {solution['overall_rating']}/5")
                                                    st.write(f"Code quality: {solution['code_quality']}/5")
                                                    st.write(f"Explanation rating: {solution['explanation_rating']}/5")
                                                    st.write(solution['reason'])
                                                # st.video(get_video_url_from_firebase("recording.mp4"))
                                                # st.audio(get_video_url_from_firebase("explanation.mp3"))
# Run the Streamlit appx
if __name__ == '__main__':
    initialize_app()
    
    if st.session_state.is_authenticated and st.session_state.role == "recruiter":
        my_tests()
    else:
        switch_page('home')