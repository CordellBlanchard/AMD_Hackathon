import sarif
from sarif import loader
import re
import os

def file_name_to_date(file_name):
    date_pattern = r'(\d{4}-\d{2}-\d{2})'
    match = re.search(date_pattern, file_name)
    if match:
        return match.group(1)
    return None

def scan_for_sarif(dir_path):
    sarif_files = []
    for file in os.listdir(dir_path):
        if file.endswith('.sarif'):
            sarif_files.append((file_name_to_date(file), file))
            # sort sarif_files by date ascending
    return sorted(sarif_files)

def parse_sarif_file(file_path):
    sarif_data = loader.load_sarif_file(file_path)  

    commit = file_path.split('database')[-1].split('-')[1] 

    # maybe check if date is succesfully extracted, None indicates failure
    date = file_name_to_date(file_path)
    
    unique_results = {} 
    rules_broken = {}

    for run in sarif_data.runs: 
        for result in run.get_results():  

            id = result['partialFingerprints']['primaryLocationLineHash']

            if unique_results.get(id) is not None:  
                unique_results[id]['files'].append(result['locations'][0]['physicalLocation']['artifactLocation']['uri'])
                unique_results[id]['lines'].append(result['locations'][0]['physicalLocation']['region']['startLine']) 
                unique_results[id]['start_columns'].append(result['locations'][0]['physicalLocation']['region']['startColumn']) 
                unique_results[id]['end_columns'].append(result['locations'][0]['physicalLocation']['region']['endColumn'])


            else:  
                unique_results[id]  = {} 
                unique_results[id]['files'] = [result['locations'][0]['physicalLocation']['artifactLocation']['uri']]
                unique_results[id]['lines'] = [result['locations'][0]['physicalLocation']['region']['startLine']]
                unique_results[id]['start_columns'] = [result['locations'][0]['physicalLocation']['region']['startColumn']]
                unique_results[id]['end_columns'] = [result['locations'][0]['physicalLocation']['region']['endColumn']]
                unique_results[id]['ruleId'] = result['ruleId']
                unique_results[id]['description'] = result['message']['text']
                unique_results[id]['commit'] = commit  
                unique_results[id]['date'] = date
                unique_results[id]['resolved'] = False
                # unique_results[id]['resolved_commit'] = None

        rules_broken_list = run.run_data["tool"]["driver"]["rules"]
        rules_broken.update({rule['id']: rule for rule in rules_broken_list})
    
    return unique_results, rules_broken

def update_old_state(new_state: dict, old_state: dict): 
    for key in old_state.keys(): 
        if new_state.get(key) is not None: 
            old_state[key] = new_state[key] 
            new_state.pop(key) 
        else: 
            old_state[key]['resolved'] = True 
            # old_state[key]['resolved_commit'] = new_state[key]['commit'] 

    # If new_state is not empty, append to old_state
    if new_state: 
        for key in new_state.keys(): 
            old_state[key] = new_state[key]
    
    return old_state 

def get_updated_state(old_file_path: str, new_file_path: str): 
    old_results, _ = parse_sarif_file(old_file_path) 
    unique_results, _ = parse_sarif_file(new_file_path) 
    latest_dict = update_old_state(unique_results, old_results)

    return latest_dict 
           

if __name__ == "__main__":

    sarif_file_name = 'backend/app/database/database-d25dd807485c-2020-01-03.sarif'
    old_sarif_file_name = 'backend/app/database/database-b8b8ebcf851d-2017-04-11.sarif' 
    latest_dict = get_updated_state(old_sarif_file_name, sarif_file_name) 
    _, rules = parse_sarif_file(sarif_file_name) 
    print(rules) 

    # print(latest_dict)



 