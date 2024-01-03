import streamlit as st
import pandas as pd
import lmql
import requests
import time
import os
from config import OPENAI_API_KEY, MJ_API_KEY
 
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

IMAGINE_ENDPOINT = "https://api.midjourneyapi.xyz/mj/v2/imagine"
FETCH_ENDPOINT = "https://api.midjourneyapi.xyz/mj/v2/fetch"
UPSCALE_ENDPOINT = "https://api.midjourneyapi.xyz/mj/v2/upscale"
VARIATE_ENDPOINT = "https://api.midjourneyapi.xyz/mj/v2/variation"
REROLL_ENDPOINT = "https://api.midjourneyapi.xyz/mj/v2/reroll"

mj_headers = {
    "X-API-KEY": MJ_API_KEY
}

@lmql.query(model="openai/gpt-3.5-turbo-instruct")
def get_characters(book, author="", num_chars=5):
    '''lmql
    """Answering the following questions about the book {book} by {author}:

    Here's a list of major characters from the book: \n"""
    chars=[]
    for i in range(num_chars):
        "-[CHARACTER]" where STOPS_AT(CHARACTER, "\n")
        chars.append(CHARACTER.strip())
    return chars
    '''

@lmql.query(model="gpt-4")
def get_character_description(character, book, author):
    '''lmql
    """Here's an accurate and concise visual description of {character} from {book} by {author} which can be used to paint their portrait, broken down into face, hair, expression, attire, accessories, and background (don't use the words 'thick' or 'tied up' or 'bare' or 'bathing'): [DESCRIPTION]"""
    '''
 
def get_mj_prompt(character, book_name, character_description):
    """Generates a prompt for Midjourney"""
    return f"Square portrait of {character} from {book_name}. Painting style. Detailed and realistic. Fine detailed textures of the skin and clothing. Strong interplay of light and shadow. {character_description}"

def make_mj_api_call(endpoint, data, headers=mj_headers):
    """Generic function to make an API call to Midjourney"""
    response = requests.post(endpoint, headers=headers, json=data)
    return response.json()
 
def mj_imagine(prompt):
    """Generates an image from a prompt"""
    data = {
        "prompt": prompt[:1900] + " --v 6.0",
        "skip_prompt_check": True
    }
    return make_mj_api_call(IMAGINE_ENDPOINT, data)

def mj_fetch(task_id):
    """Gets the status of a task"""
    data = {"task_id": task_id}
    return make_mj_api_call(FETCH_ENDPOINT, data)

def mj_upscale(task_id, index):
    """Upscales an image"""
    data = {
        "origin_task_id": task_id,
        "index": index
    }
    return make_mj_api_call(UPSCALE_ENDPOINT, data)

def mj_variate(task_id, index):
    """Variates an image"""
    data = {
        "origin_task_id": task_id,
        "index": index
    }
    return make_mj_api_call(VARIATE_ENDPOINT, data)
        
def mj_reroll(task_id):
    """Rerolls an image"""
    data = {"origin_task_id": task_id}
    return make_mj_api_call(REROLL_ENDPOINT, data)

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

st.set_page_config(layout="wide", page_icon="🧙‍♂️", page_title="Melquíades - Novel Character Visualizer")
st.title("🧙🏽‍♂️ Melquíades - Novel Character Visualizer")

book_name = st.text_input("Enter the name of the book:", value="One Hundred Years of Solitude")
book_author = st.text_input("Enter the author of the book:")

st.markdown("## Characters")

num_characters = st.slider("Select the number of characters:", min_value=1, max_value=30, value=5)

if 'df' in st.session_state:
    df = st.session_state['df']
else:
    df = pd.DataFrame()

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Fetch Characters"):
        clear_cache()
        characters = get_characters(book_name, book_author, num_characters)
        df = pd.DataFrame()
        df['Character'] = characters
        st.session_state['df'] = df
    
with col2:
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
    if st.button("Visualise Characters"):
        if 'Description' in df.columns and df['Description'].notna().any():
            def condition_function(row):
                return len(row['Description']) > 0

            def task_function(row):
                return mj_imagine(row['Description'])

            def final_callback():
                df['Reroll'] = False
                df['Upscale'] = "None"
                df['Variate'] = "None"

            process_tasks(df, condition_function, task_function, final_callback,  "Visualising characters")
        else:
            st.error("Please describe characters first.")

col4, col5, col6 = st.columns(3)

with col4:
    if st.button("Reroll selected"):
        def condition_function(row):
            return row['Reroll'] and row['Task ID'] != ""

        def task_function(row):
            return mj_reroll(row['Task ID'])

        def final_callback():
            df['Reroll'] = False

        process_tasks(df, condition_function, task_function, final_callback, "Rerolling characters")
    
with col5:
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
    if st.button("Variate selected"):
        def condition_function(row):
            return row['Variate'] != "None" and not pd.isna(row['Variate'])

        def task_function(row):
            return mj_variate(row['Task ID'], str(int(row['Variate'])))

        def final_callback():
            df['Variate'] = "None"

        process_tasks(df, condition_function, task_function, final_callback, "Variating characters")

if 'df' in globals() and not df.empty:
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
