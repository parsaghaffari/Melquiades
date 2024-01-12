import os
import lmql

from config import OPENAI_API_KEY 
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

def type_prompt(type):
    """Returns the prompt for the given type of entity"""
    if type == "characters":
        return "characters"
    elif type == "places":
        return "places (such as prominent buildings, landmarks, or locations)"
    elif type == "events":
        return "events (or epic scenes)"    

@lmql.query(model="openai/gpt-3.5-turbo-instruct")
def get_things(thing_type, book, author="", num_things=5):
    '''lmql
    """Answering the following questions about the book {book} by {author}:

    Here's a list of major {type_prompt(thing_type)} from the book: \n"""
    things=[]
    for i in range(num_things):
        "-[THING]" where STOPS_AT(THING, "\n")
        things.append(THING.strip())
    return things
    '''

def get_thing_description(type, thing, book, author):
    if type == "characters":
        return get_character_description(thing, book, author)
    elif type == "places":
        return get_place_description(thing, book, author)
    elif type == "events":
        return get_event_description(thing, book, author)

@lmql.query(model="gpt-4")
def get_character_description(character, book, author):
    '''lmql
    """Here's an accurate and concise visual description of {character} from {book} by {author} which can be used to paint their portrait, broken down into face, hair, expression, attire, accessories, and background: [DESCRIPTION]"""
    '''
    
@lmql.query(model="gpt-4")
def get_place_description(place, book, author):
    '''lmql
    """Here's an accurate and concise visual description of the place "{place}" from {book} by {author} which can be used as instructions for a painter to paint it with a high level of accuracy and detail. Break down the instructions into meaningful headings (such as visible buildings, background, characters, etc): [DESCRIPTION]"""
    '''
    
@lmql.query(model="gpt-4")
def get_event_description(event, book, author):
    '''lmql
    """Here's an accurate and concise visual description of the scene "{event}" from {book} by {author} which can be used as instructions for a painter to paint it with a high level of accuracy and detail. Break down the instructions into meaningful headings (such as characters, their facial expressions, prominent landmarks, etc): [DESCRIPTION]"""
    '''