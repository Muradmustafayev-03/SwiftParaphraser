from .text import add_missing_imports
from .secret import *
import openai
import json

openai.api_key = OPENAI_KEY
openai.organization = ORGANIZATION


def gpt_response(prompt: str, system: str, temperature: float = 1.0):
    res = openai.ChatCompletion.create(
        model='gpt-3.5-turbo-16k',
        messages=[
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': prompt}
        ],
        temperature=temperature
    )
    return json.loads(str(res))['choices'][0]['message']['content']


def generate_rename_map(names: list, temperature: float = 1.2):
    system = 'The user will give you the list of names to rename. ' \
             'The input will be in the following form: ' \
             '[\'name1\', \'name2\', ...]. ' \
             'You must think of alternative names and provide the output in the form: ' \
             '{"name1": "alt_name1", "name2": "name2ButDifferent", ...}. ' \
             'Your response should only consist of a parsable json string as demonstrated above.' \
             'Longer names are generally better, but they can be arbitrary long.'
    prompt = str(names)

    response = gpt_response(prompt, system, temperature)
    return json.loads(response)


def add_comments(code: str, temperature: float = 1.0):
    system = 'The user will give you the swift code. ' \
             'Add as many comments to the code as possible. ' \
             'The more comments the better. The larger comment blocks are the better.' \
             'The more detailed the comments are the better.' \
             'Your response must only consist of the user\'s code with your added comments.' \
             'Do not make any changes within the code, only add the comments.' \
             'Your entire unchanged response will be writen to the .swift file.' \
             'If you want to add something, write it in the comments.'

    response = gpt_response(code, system, temperature).replace('```', '//------------------------')
    response = add_missing_imports(code, response)
    return response


def gpt_modify(code: str, temperature: float = 1.0):
    system = 'You will be given a swift code. Modify the inner structure of this code ' \
             'keeping its behaviour the same. Do not make any assumptions about the code, ' \
             'make only the local changes that do not affect the other references to the code. ' \
             'For the code inside the functions, make it seem more complicated, but not changing ' \
             'its actual functionality. Your response must only consist of the code.' \

    response = gpt_response(code, system, temperature).replace('```', '//------------------------')
    response = add_missing_imports(code, response)
    return response


def fix_syntax(code: str, temperature: float = 1.0):
    system = 'You will be given a swift code. If there are any syntax errors in the code' \
             'such as missing ; or missing closing brackets, fix those errors and give the' \
             'corrected code in the response. If you did not find any errors, give the source ' \
             'code unchanged. Your response must only consist of the code. RESPOND WITH CODE ONLY!' \

    response = gpt_response(code, system, temperature).replace('```', '//------------------------')
    response = add_missing_imports(code, response)
    return response