from .text import add_missing_imports, remove_comments, remove_whitespace
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


def add_comments(code: str, temperature: float = 1.0):
    system = 'The user will give you the swift code. ' \
             'Add as many comments to the code as possible. ' \
             'The more comments the better. The larger comment blocks are the better.' \
             'The more detailed the comments are the better.' \
             'Your response must only consist of the user\'s code with your added comments.' \
             'Do not dare to make any changes within the code, only add the comments.' \
             'Your entire unchanged response will be writen to the .swift file.' \

    for _ in range(5):
        try:
            response = gpt_response(code, system, temperature)
        except Exception as e:
            print(e, e.__class__)
            print('Commenting failed. Trying again...')
            continue
        if '```' in response:
            # extract code from response
            response = response.split('```')[1]
        response = add_missing_imports(code, response)

        clean_code = remove_whitespace(remove_comments(code))
        clean_response = remove_whitespace(remove_comments(response))
        left_diff = [char1 for char1, char2 in zip(clean_code, clean_response) if char1 != char2]
        right_diff = [char2 for char1, char2 in zip(clean_code, clean_response) if char1 != char2]
        difference = left_diff + right_diff

        if not difference:
            return response
        else:
            print('Commenting failed. Trying again...')
    print('Returned code with no comments')
    return code


def gpt_modify(code: str, temperature: float = 1.0):
    system = 'You will be given a swift code. Modify the inner structure of this code ' \
             'keeping its behaviour the same. Do not make any assumptions about the code, ' \
             'make only the local changes that do not affect the other references to the code. ' \

    response = gpt_response(code, system, temperature)
    if '```' in response:
        # extract code from response
        response = response.split('```')[1]
    response = add_missing_imports(code, response)
    return response


def fix_syntax(code: str, temperature: float = 1.0):
    system = 'You will be given a swift code. If there are any syntax errors in the code' \
             'such as missing ; or missing closing brackets, fix those errors and give the' \
             'corrected code in the response. If you did not find any errors, give the source ' \
             'code unchanged. Your response must only consist of the code. RESPOND WITH CODE ONLY!' \

    response = gpt_response(code, system, temperature)
    if '```' in response:
        # extract code from response
        response = response.split('```')[1]
    response = add_missing_imports(code, response)
    return response
