import streamlit as st
import pandas as pd
import time

from midjourney_api import *
from lmql_queries import *

def clear_cache():
    """Clears the session state"""
    for key in st.session_state.keys():
        del st.session_state[key]

def process_tasks(df, condition_function, task_function, callback, 
                  progress_text, result_status_col='Processing Status', result_url_col='Img URL', update_task_id=True):
    tasks = []

    for i, row in df.iterrows():
        if condition_function(row):
            task = task_function(row)
            tasks.append(task)
            if update_task_id:
                if 'status' in task:
                    df.loc[i, 'Submission Status'] = f"{task['status']} - {task['message']}" if len(task['message']) > 0 else task['status']
                    df.loc[i, 'Task ID'] = task['task_id']
                else:
                    st.info(json.dumps(task, indent=4))
                    df.loc[i, 'Submission Status'] = "failed - no status"
                    df.loc[i, 'Task ID'] = ""
        else:
            tasks.append(None)

    if any(x is not None for x in tasks):
        progress = st.progress(0.0, text=progress_text)
        while True:
            for i, task in enumerate(tasks):
                if task is not None and 'status' in task and task['status'] == "success":
                    pstatus = mj_fetch(task['task_id'])
                    df.loc[i, result_status_col] = pstatus['status']
                    df.loc[i, result_url_col] = pstatus['task_result']['image_url']

            st.session_state['df'] = df

            done_tasks = ((df[result_status_col] != "processing") & (df[result_status_col] != "pending"))
            all_tasks = (df[result_status_col] != "")
            progress.progress(max(0.01, done_tasks.sum()/all_tasks.sum()), text=progress_text)

            if done_tasks.all() == True:
                progress.empty()
                break

            time.sleep(5)
        
        callback()

if 'df' in st.session_state:
    df = st.session_state['df']
else:
    df = pd.DataFrame()

st.set_page_config(layout="wide", page_icon="🧙‍♂️", page_title="Melquíades - Novel Visualiser")
st.title("🧙🏽‍♂️ Melquíades - Novel Visualiser")

book_name = st.text_input("Enter the name of the book:", value="One Hundred Years of Solitude")
book_author = st.text_input("Enter the author of the book:")

css = """
.st-emotion-cache-1r6slb0 {
    border: 1px solid #ccc;
    padding: 10px;
}
"""
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
 
with col1:
    f"""1. **Fetch things**: Start by fetching some things (characters, places, or events) from the book. Select a number using the slider below, and click on 'Fetch character/place/event'.
    
    Note: You can also edit the things in the table below. You can change their names, or add/remove things.
    """
    vis_mode = st.selectbox('What shall we visualise?', ('characters', 'places', 'events'))
    num_things = st.slider(f"Select the number of {vis_mode} to fetch:", min_value=1, max_value=30, value=5)
    if st.button(f"Fetch {vis_mode}"):
        clear_cache()
        things = get_things(vis_mode, book_name, book_author, num_things)
        df = pd.DataFrame()
        df['Things'] = things
        st.session_state['df'] = df
    
with col2:
    f"""2. **Describe {vis_mode}**: Now that you have some {vis_mode}, describe them using the button below.
    
    Note: You can also edit the descriptions in the table below."""
    if st.button(f"Describe {vis_mode}"):
        if 'Things' in df.columns and df['Things'].notna().any():
            progress = st.progress(0.0, text=f"Describing {vis_mode}")
            things = df['Things']
            descriptions = []
            for i, thing in enumerate(things):
                progress.progress(max(0.01, i/len(things)), text=f"Describing {vis_mode} {i+1} out of {len(things)} ({thing})")
                description = get_thing_description(vis_mode, thing, book_name, book_author).variables['DESCRIPTION']
                prompt = get_mj_prompt(vis_mode, thing, book_name, description)
                descriptions.append(prompt)
            progress.empty()
            df['Description'] = descriptions
            st.session_state['df'] = df
        else:
            st.error("Please fetch some things first!")

with col3:
    f"""3. **Visualise {vis_mode}**: Now that you have some descriptions for your {vis_mode}, visualise them using the button below. This will take a while, so please be patient."""
    col31, col32, col33 = st.columns(3)
    
    with col31: stylize = st.slider("Stylize:", min_value=0, max_value=1000, value=100)
    with col32: chaos = st.slider("Chaos:", min_value=0, max_value=100, value=0)
    with col33: weird = st.slider("Weird:", min_value=0, max_value=3000, value=0)
    aspect_ratio = st.selectbox('Aspect ratio:', ('1:1', '5:4', '7:4'))
    if st.button(f"Visualise {vis_mode}"):
        if 'Description' in df.columns and df['Description'].notna().any():
            def condition_function(row):
                return len(row['Description']) > 0

            def task_function(row):
                return mj_imagine(row['Description'], stylize, chaos, weird, aspect_ratio)

            def final_callback():
                df['Reroll'] = False
                df['Upscale'] = "None"
                df['Variate'] = "None"

            process_tasks(df, condition_function, task_function, final_callback,  f"Visualising {vis_mode}")
        else:
            st.error(f"Please describe {vis_mode} first.")

col4, col5, col6 = st.columns(3)

with col4:
    """4. **Reroll selected**: If you don't like the visualisations, you can regenerate them using the button below. Tick the box next to the items you want to reroll, and click on 'Reroll selected'. The results will appear in the 'Img URL' column."""
    if st.button("Reroll selected"):
        def condition_function(row):
            return row['Reroll'] and row['Task ID'] != ""

        def task_function(row):
            return mj_reroll(row['Task ID'])

        def final_callback():
            df['Reroll'] = False

        process_tasks(df, condition_function, task_function, final_callback, f"Rerolling {vis_mode}")
    
with col5:
    """5. **Upscale selected**: If you want to see a higher resolution and singular version of a visualisation, you can upscale it using the button below. Select the index of the image you want to upscale (1/2/3/4), and click on 'Upscale selected'. The results will appear in the 'Upscale Img URL' column."""
    if st.button("Upscale selected"): 
        def condition_function(row):
            return row['Upscale'] != "None" and not pd.isna(row['Upscale'])

        def task_function(row):
            return mj_upscale(row['Task ID'], str(int(row['Upscale'])))

        def final_callback():
            df['Upscale'] = "None"

        process_tasks(df, condition_function, task_function, final_callback, 
                      f"Upscaling {vis_mode}", 'Upscale Processing Status', 'Upscale Img URL', False)

with col6:
    """6. **Variate selected**: If you want to see a variation of the visualisation, you can variate it using the button below. Select the index of the image you want to variate (1/2/3/4), and click on 'Variate selected'. The results will appear in the 'Img URL' column."""
    if st.button("Variate selected"):
        def condition_function(row):
            return row['Variate'] != "None" and not pd.isna(row['Variate'])

        def task_function(row):
            return mj_variate(row['Task ID'], str(int(row['Variate'])))

        def final_callback():
            df['Variate'] = "None"

        process_tasks(df, condition_function, task_function, final_callback, f"Variating {vis_mode}")

if 'df' in globals() and not df.empty:
    """### Results"""
    edited_df = st.data_editor(df, use_container_width=True, column_config={
            "Img URL": st.column_config.LinkColumn(),
            "Upscale Img URL": st.column_config.LinkColumn(),
            "Variate Img URL": st.column_config.LinkColumn(),
            # "Submission Status": None,
            # "Task ID": None,
            "Reroll": st.column_config.CheckboxColumn(
                "Reroll an image",
                default=False
            ),
            "Upscale": st.column_config.SelectboxColumn(
                help="The index of the image to upscale (1/2/3/4)",
                options=["None","1","2","3","4"],
                required=True
            ),
            "Variate": st.column_config.SelectboxColumn(
                help="The index of the image to variate (1/2/3/4)",
                options=["None","1","2","3","4"],
                required=True
            )
        },
        hide_index=True, num_rows="dynamic", disabled=("Submission Status", "Task ID", "Processing Status", "Img URL", "Upscale Img URL", "Upscale Processing Status", "Variate Img URL", "Variate Processing Status"))
    st.session_state['df'] = edited_df.reset_index(drop=True)
