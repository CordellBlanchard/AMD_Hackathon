from app.util.blame_api import Repo, getLineInfo, getFullHashFromPartial
from app.util.sarif_parser import parse_sarif_file 
import os 
import requests
from openai import OpenAI
from time import perf_counter 
import json 
from app import db 
from flask import jsonify 
from tenacity import retry, stop_after_attempt, wait_fixed
from app.models.models import Issue, Blame, LLMCache  
import re

OPENAI_API_KEY = 'OPENAI API KEY HERE' 
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_openai_response(prompt: str): 
    headers = { 
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are an expert Python code-fixing developer. You are helping a junior developer fix a bug in their code. You are acting as a code-fixing assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2000,
        "temperature": 0.7,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }

    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=data)  # Disable SSL verification
        response.raise_for_status()  # Raise an error for bad status codes
        response = response.json()["choices"][0]["message"]["content"].strip()

        # Regular expression to match the content between 1), 2), and 3)
        pattern = re.compile(r"1\)(.*?)2\)(.*?)3\)(.*)", re.DOTALL)
        
        # Search the response using the pattern
        match = pattern.search(response)
        
        if match:
            fix = match.group(2).strip()
            explanation = match.group(3).strip()

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

    return response, fix, explanation

def get_llm_response(rule_info: str, issue_message: str, file: str, line: int, commit_hash: str):  

    ''' 
    rule_info: Description of the rule violated (From rules) 
    issue_message: "description" message in the issue instance 
    file: SARIF File Path Name 
    line: specific line number 
    commit_hash: full commit hash
    
    '''

    repo = Repo("tensorflow", "tensorflow") 

    print('GENERATING CODE CONTEXT')

    commit_hash = getFullHashFromPartial(repo, commit_hash)

    print(commit_hash)

    # Use 5 lines above and below the line to get the context 
    codes = [] 
    for i in range(-5, 5): 
        blame, line_content = getLineInfo(repo, commit_hash, file, line+i) 
        codes.append(line_content) 
    
    code_context = "\n".join(codes) 
                        
    prompt=f"""
    Issue Description: {rule_info} 

    The specific context of the rule violation is: {issue_message}

    The problematic line of code is: {codes[5]}

    Below is the code context around the problematic line:
    {code_context}

    Please structure your answer in three points: 
    1) Explain the issue in the code context provided.
    1) suggest a fix for the above code context based on the issue described. 
    2) Explain why your fix is the best solution for the issue.
    """

    print('STARTING QUERYING')

    # Call GPT4 
    start = perf_counter() 

    response = get_openai_response(prompt)

    print('FINISHED QUERYING')

    # suggestion = response.choices[0].message.content.strip() 

    return response 

def create_cache(blame_id, response):  

    '''
    Creates a cache entry for the LLM response.
    '''
    
    blame = Blame.query.get(blame_id) 
    if not blame: 
        print(f"No Blame entry found with id {blame_id}")
        return 

    # Create a new LLMCache object 
    llm_cache_entry = LLMCache(suggestion=response, blame_id=blame_id, blame=blame) 
    db.session.add(llm_cache_entry) 
    db.session.commit()


def test(sarif_path: str, llm_report_path = 'llm_report.txt'): 

    '''
    Creates initial GPT fix for the issues in the SARIF file. 
    '''

    sarif_path = '../database/database-5a7786812dd4-2024-01-11.sarif' 
    sarif_data, rules = parse_sarif_file(sarif_path)    

    rules_dict = {} 
    for rule_id, rule_data in rules.items(): 
        rules_dict[rule_id] = rule_data['fullDescription']['text']

    repo = Repo("tensorflow", "tensorflow")  

    with open(llm_report_path, 'w') as f: 
        for issue_id, issue_info in sarif_data.items(): 
            
            file = issue_info['files'][0]
            line = issue_info['lines'][0] 

            print(file, line) 

            print('Starting to generate fix for issue: ', issue_info['ruleId'])
                                
            response = get_llm_response(rules_dict[issue_info['ruleId']], issue_info['description'], file, line, issue_info['commit'])

            f.write("----------------------------------------------------\n")
            f.write(f"Issue ID: {issue_id}\n")
            f.write(f"Rule Violated: {issue_info['ruleId']}\n")
            f.write(f"Rule Description: {rules_dict[issue_info['ruleId']]}\n")
            f.write(f"Suggested fix: {response}\n\n") 
            f.write("----------------------------------------------------\n")

            print('Successfully generated fix for issue: ', issue_info['ruleId']) 

            break 

if __name__ == '__main__': 
    test('C:\\Users\\lakgupta\\Documents\\Hackathon\\AMD_Hackathon\\backend\\app\\databasedatabase-5a7786812dd4-2024-01-11.sarif')