# Melquíades

A [Streamlit](https://streamlit.io/) app for visualising your favourite novels using GPT and Midjourney. 

<img width="1180" alt="_melquiades" src="https://github.com/parsaghaffari/Melquiades/assets/3098913/9e394ebf-2fd4-4c6d-8e53-c7af85a5d1a9">

Read more about it on my blog: [blog post](https://parsabg.com/visualising-novels-using-midjourney-v6-and-gpt-4-part-1-characters)

## Prerequisites

To run Melquíades, you will need credentials for two APIs:

1. OpenAI: Sign up [here](https://platform.openai.com/signup) and get your API key.
2. GoAPI: An unofficial/3rd party API for Midjourney which you can sign up for [here](https://www.goapi.ai/midjourney-api).

## Running locally

1. Install the dependencies: `pip install pandas streamlit`.
2. Copy `config.example.py` to `config.py` and insert your OpenAI and GoAPI API keys.
3. Run `streamlit run app.py`
