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
                df.loc[i, 'Submission Status'] = f"{task['status']} - {task['message']}" if len(task['message']) > 0 else task['status']
                df.loc[i, 'Task ID'] = task['task_id']
        else:
            tasks.append(None)

    if any(x is not None for x in tasks):
        progress = st.progress(0.0, text=progress_text)
        while True:
            for i, task in enumerate(tasks):
                if task is not None and task['status'] == "success":
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

st.set_page_config(layout="wide", page_icon="🧙‍♂️", page_title="Melquíades - Novel Character Visualiser")
st.title("🧙🏽‍♂️ Melquíades - Novel Character Visualiser")

book_name = st.text_input("Enter the name of the book:", value="One Hundred Years of Solitude")
book_author = st.text_input("Enter the author of the book:")

st.markdown("## Characters")

col1, col2, col3 = st.columns(3)

with col1:
    """1. **Fetch characters**: Start by fetching some characters from the book. Select a number using the slider below, and click on 'Fetch Characters'.
    
    Note: You can also edit the characters in the table below. You can change their names, or add/remove characters.
    """
    num_characters = st.slider("Select the number of characters to fetch:", min_value=1, max_value=30, value=5)
    if st.button("Fetch Characters"):
        clear_cache()
        characters = get_characters(book_name, book_author, num_characters)
        df = pd.DataFrame()
        df['Character'] = characters
        st.session_state['df'] = df
    
with col2:
    """2. **Describe characters**: Now that you have some characters, describe them using the button below.
    
    Note: You can also edit the descriptions in the table below."""
    if st.button("Describe Characters"):
        if 'Character' in df.columns and df['Character'].notna().any():
            progress = st.progress(0.0, text="Describing characters")
            characters = df['Character']
            descriptions = []
            for i, character in enumerate(characters):
                progress.progress(max(0.01, i/len(characters)), text=f"Describing character {i+1} out of {len(characters)} ({character})")
                description = get_character_description(character, book_name, book_author).variables['DESCRIPTION']
                prompt = get_mj_prompt(character, book_name, description)
                descriptions.append(prompt)
            progress.empty()
            df['Description'] = descriptions
            st.session_state['df'] = df
        else:
            st.error("Please fetch characters first.")

with col3:
    """3. **Visualise characters**: Now that you have some character descriptions, visualise them using the button below. This will take a while, so please be patient."""
    col31, col32, col33 = st.columns(3)
    
    with col31: stylize = st.slider("Stylize:", min_value=0, max_value=1000, value=100)
    with col32: chaos = st.slider("Chaos:", min_value=0, max_value=100, value=0)
    with col33: weird = st.slider("Weird:", min_value=0, max_value=3000, value=0)
    if st.button("Visualise Characters"):
        if 'Description' in df.columns and df['Description'].notna().any():
            def condition_function(row):
                return len(row['Description']) > 0

            def task_function(row):
                return mj_imagine(row['Description'], stylize, chaos, weird)

            def final_callback():
                df['Reroll'] = False
                df['Upscale'] = "None"
                df['Variate'] = "None"

            process_tasks(df, condition_function, task_function, final_callback,  "Visualising characters")
        else:
            st.error("Please describe characters first.")

col4, col5, col6 = st.columns(3)

with col4:
    """4. **Reroll selected**: If you don't like the visualisation of a character, you can reroll it using the button below. Tick the box next to the characters you want to reroll, and click on 'Reroll selected'. The results will appear in the 'Img URL' column."""
    if st.button("Reroll selected"):
        def condition_function(row):
            return row['Reroll'] and row['Task ID'] != ""

        def task_function(row):
            return mj_reroll(row['Task ID'])

        def final_callback():
            df['Reroll'] = False

        process_tasks(df, condition_function, task_function, final_callback, "Rerolling characters")
    
with col5:
    """5. **Upscale selected**: If you want to see a higher resolution version of the visualisation of a character, you can upscale it using the button below. Select the index of the image you want to upscale (1/2/3/4), and click on 'Upscale selected'. The results will appear in the 'Upscale Img URL' column."""
    if st.button("Upscale selected"): 
        def condition_function(row):
            return row['Upscale'] != "None" and not pd.isna(row['Upscale'])

        def task_function(row):
            return mj_upscale(row['Task ID'], str(int(row['Upscale'])))

        def final_callback():
            df['Upscale'] = "None"

        process_tasks(df, condition_function, task_function, final_callback, 
                      "Upscaling characters", 'Upscale Processing Status', 'Upscale Img URL', False)

with col6:
    """6. **Variate selected**: If you want to see a variation of the visualisation of a character, you can variate it using the button below. Select the index of the image you want to variate (1/2/3/4), and click on 'Variate selected'. The results will appear in the 'Img URL' column."""
    if st.button("Variate selected"):
        def condition_function(row):
            return row['Variate'] != "None" and not pd.isna(row['Variate'])

        def task_function(row):
            return mj_variate(row['Task ID'], str(int(row['Variate'])))

        def final_callback():
            df['Variate'] = "None"

        process_tasks(df, condition_function, task_function, final_callback, "Variating characters")

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
