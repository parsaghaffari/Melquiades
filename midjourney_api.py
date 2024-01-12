import requests
import json
from config import MJ_API_KEY

IMAGINE_ENDPOINT = "https://api.midjourneyapi.xyz/mj/v2/imagine"
FETCH_ENDPOINT = "https://api.midjourneyapi.xyz/mj/v2/fetch"
UPSCALE_ENDPOINT = "https://api.midjourneyapi.xyz/mj/v2/upscale"
VARIATE_ENDPOINT = "https://api.midjourneyapi.xyz/mj/v2/variation"
REROLL_ENDPOINT = "https://api.midjourneyapi.xyz/mj/v2/reroll"

mj_headers = {
    "X-API-KEY": MJ_API_KEY
}

def get_mj_prompt(type, thing, book_name, description):
    """Generates a prompt for Midjourney"""
    if type == "characters":
        return f"Square portrait of {thing} from {book_name}. Painting style. Detailed and realistic. Fine detailed textures of the skin and clothing. Strong interplay of light and shadow. {description}"
    elif type == "places":
        return f"A portrait of {thing} from {book_name}. Painting style. Detailed and realistic. Fine detailed textures. Strong interplay of light and shadow. {description}"
    elif type == "events":
        return f"A portrait of {thing} from {book_name}. Painting style. Detailed and realistic. Fine detailed textures. Strong interplay of light and shadow. {description}"

def make_mj_api_call(endpoint, data, headers=mj_headers):
    """Generic function to make an API call to Midjourney"""
    try:
        response = requests.post(endpoint, headers=headers, json=data)
        return response.json()
    except json.JSONDecodeError:
        print(f"JSONDecodeError: {response.text}")
        return {"status": "failed", "message": "JSONDecodeError", "task_id": None}
 
def mj_imagine(prompt, stylize=100, chaos=0, weird=0, aspect_ratio="1:1"):
    """Generates an image from a prompt"""
    data = {
        "prompt": prompt[:1900] + f"--stylize {stylize} --chaos {chaos} --weird {weird} --v 6.0 --ar {aspect_ratio}",
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