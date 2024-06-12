import sarif
from sarif import loader


def parse_sarif_file(file_path):
    sarif_data = loader.load_sarif_file(file_path)  

    commit = file_path.split('database')[-1].split('-')[1]

    unique_results = {} 

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
                unique_results[id]['rule'] = result['rule']['id']
                unique_results[id]['description'] = result['message']['text']
                unique_results[id]['commit'] = commit 
                unique_results[id]['resolved'] = False
    
    return unique_results

def update_old_state(new_state: dict, old_state: dict): 
    for key in new_state.keys(): 
        if old_state.get(key) is not None: 
            old_state['key']['resolved'] = True 

        else: 
            old_state[key] = new_state[key]  
    
    return old_state 
           

if __name__ == "__main__":

    sarif_file_name = '../database/database-d25dd807485c-2020-01-03.sarif'
    unique_results = parse_sarif_file(sarif_file_name) 

    print(unique_results['64ec0e96e96c3fde:1'])




 