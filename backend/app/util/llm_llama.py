from blame_api import Repo, getLineInfo, getFullHashFromPartial
from sarif_parser import parse_sarif_file 
import os 
from openai import OpenAI
from time import perf_counter 
import json 
# from app import db 
from flask import jsonify  

from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline 
from langchain_core.prompts import PromptTemplate 
from langchain.chains import LLMChain

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline 
from huggingface_hub import login 


login(token = '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')

# from app.models.models import Issue, Blame, LLMCache  

huggingface_token = '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'
model_name = "daryl149/Llama-2-7b-chat-hf"  # Use the appropriate model name

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, token=huggingface_token)

# Create the pipeline
llm_pipeline = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_length=2000,
    temperature=0.7,
    do_sample = True,
    top_p=1,
    token = huggingface_token
)

# Define the template and chain
# Define the template
template = """
Issue Description: {rule_info}

The specific context of the rule violation is: {issue_message}

The problematic line of code is: {error_line}

Below is the code context around the problematic line:
{code_context}

Please structure your answer in three points: 
1) Explain the issue in the code context provided.
2) Suggest a fix for the above code context based on the issue described. 
3) Explain why your fix is the best solution for the issue.
"""

prompt_template = PromptTemplate(
    input_variables=["rule_info", "issue_message", "error_line", "code_context"],
    template=template,
)

llm = HuggingFacePipeline(pipeline=llm_pipeline)
chain = LLMChain(llm=llm, prompt=prompt_template)

def get_llm_response(rule_info: str, issue_message: str, file: str, line: int, commit_hash: str):  
    ''' 
    rule_info: Description of the rule violated (From rules) 
    issue_message: "description" message in the issue instance 
    file: SARIF File Path Name 
    line: specific line number 
    commit_hash: full commit hash
    '''

    print(rule_info) 
    print(issue_message)
    print(file)
    print(line)
    print(commit_hash)

    repo = Repo("tensorflow", "tensorflow") 

    print('GENERATING CODE CONTEXT')

    commit_hash = getFullHashFromPartial(repo, commit_hash)
    print(commit_hash)

    # Use 5 lines above and below the line to get the context 
    codes = [] 
    for i in range(-5, 6):  # Changed to -5 to 5 to get 11 lines, centered on the line of interest
        blame, line_content = getLineInfo(repo, commit_hash, file, line+i) 
        codes.append(line_content) 
    
    code_context = "\n".join(codes) 
    error_line = codes[5]
    
    prompt_variables = {
        "rule_info": rule_info,
        "issue_message": issue_message,
        "error_line": error_line,
        "code_context": code_context,
    }

    print('STARTING QUERYING')

    # Generate response using LangChain
    start = perf_counter() 
    response = chain.invoke(prompt_variables)
    end = perf_counter()

    print('FINISHED QUERYING')
    print(f"Time taken: {end - start:.2f} seconds")

    return response.strip()

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

            print(issue_info)
            
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