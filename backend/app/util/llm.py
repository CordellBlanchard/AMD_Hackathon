from blame_api import Repo, getLineInfo
from sarif_parser import parse_sarif_file 
import os 
from openai import OpenAI
from time import perf_counter 
import json 
from app import db
import jsonify 

from app.models.models import Issue, Blame, LLMCache

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY")) 

def get_llm_response(rule_info: str, issue_message: str, file: str, line: int, commit_hash: str):  

    ''' 
    rule_info: Description of the rule violated (From rules) 
    issue_message: "description" message in the issue instance 
    file: SARIF File Path Name 
    line: specific line number 
    commit_hash: full commit hash
    
    '''

    repo = Repo("tensorflow", "tensorflow")

    # Use 5 lines above and below the line to get the context 
    codes = [] 
    for i in range(-5, 5): 
        blame, line_content = getLineInfo(repo, commit_hash, file, line+i) 
        if i == 0: 
            print(line_content) 
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

    # Call GPT4 
    start = perf_counter() 
    response = client.chat.completions.create( 
        messages= [
            {
            "role": "system",
            "content": "You are an expert Python code-fixing developer. You are helping a junior developer fix a bug in their code. You are acting as a code-fixing assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        model="gpt-4",
        max_tokens=2000,
        temperature=0.7,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    ) 

    suggestion = response.choices[0].message.content.strip() 

    return suggestion 

def create_cache(blame_id, response):  
    
    blame = Blame.query.get(blame_id) 
    if not blame: 
        print(f"No Blame entry found with id {blame_id}")
        return 

    # Create a new LLMCache object 
    llm_cache_entry = LLMCache(suggestion=response, blame_id=blame_id, blame=blame) 
    db.session.add(llm_cache_entry) 
    db.session.commit()


def create_initial_fix(sarif_path: str, llm_report_path = 'llm_report.txt', history_path='chat_history.json'): 

    '''
    Creates initial GPT fix for the issues in the SARIF file. 
    '''

    sarif_path = '../database/database-5a7786812dd4-2024-01-11.sarif' 
    sarif_data, rules = parse_sarif_file(sarif_path)  

    repo = Repo("tensorflow", "tensorflow")  

    conversation_history = [] 

    with open(llm_report_path, 'w') as f: 
        for issue_id, issue_info in sarif_data.items(): 
            file = issue_info['files'][0]
            line = issue_info['lines'][0] 

            # Use 5 lines above and below the line to get the context 
            codes = [] 
            for i in range(-5, 5): 
                blame, line_content = getLineInfo(repo, "5a7786812dd4cb4511e8ef85b12017cf3d2ae08d", file, line+i) 
                if i == 0: 
                    print(line_content)
                codes.append(line_content) 
            
            code_context = "\n".join(codes) 

            print('Starting to generate fix for issue: ', issue_info['rule'])
                                
            prompt=f"""
            Issue Description: {rules[issue_info['rule']]} 

            The specific context of the rule violation is: {issue_info['description']}

            The problematic line of code is: {codes[5]}

            Below is the code context around the problematic line:
            {code_context}

            Please structure your answer in three points: 
            1) Explain the issue in the code context provided.
            1) suggest a fix for the above code context based on the issue described. 
            2) Explain why your fix is the best solution for the issue.
            """

            # Call GPT4 
            start = perf_counter() 
            response = client.chat.completions.create( 
                messages= [
                    {
                    "role": "system",
                    "content": "You are an expert Python code-fixing developer. You are helping a junior developer fix a bug in their code. You are acting as a code-fixing assistant."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                model="gpt-4",
                max_tokens=2000,
                temperature=0.7,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            ) 

            end = perf_counter()
            # Extract the suggestion from the response
            suggestion = response.choices[0].message.content.strip()

            f.write("----------------------------------------------------\n")
            f.write(f"Issue ID: {issue_id}\n")
            f.write(f"Rule Violated: {issue_info['rule']}\n")
            f.write(f"Rule Description: {rules[issue_info['rule']]}\n")
            f.write(f"Code Context: {codes}\n")
            f.write(f"Error Line: {codes[5]}\n")
            f.write(f"Suggested fix: {suggestion}\n\n") 
            f.write(f"Time taken to generate fix: {end-start} s\n")
            f.write("----------------------------------------------------\n")

            print('Successfully generated fix for issue: ', issue_info['rule']) 

            # Save the conversation history
            conversation_history.append({
                "role": "user",
                "content": prompt
            })
            conversation_history.append({
                "role": "assistant",
                "content": suggestion
            })

            # Save the history to a JSON file
            with open(history_path, 'w') as history_file:
                json.dump(conversation_history, history_file) 