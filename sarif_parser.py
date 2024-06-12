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
                # unique_results[id]['resolved_commit'] = None
    
    return unique_results

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
           

if __name__ == "__main__":

    sarif_file_name = '../database-d25dd807485c-2020-01-03.sarif'
    old_sarif_file_name = '../database-b8b8ebcf851d-2017-04-11.sarif'
    old_results = parse_sarif_file(old_sarif_file_name) 
    unique_results = parse_sarif_file(sarif_file_name) 

    latest_dict = update_old_state(unique_results, old_results)

    # print(old_results.keys(), '\n')
    # print(unique_results.keys(), '\n')
    # print(latest_dict.keys(), '\n')

    print(latest_dict['d451331f1f6ae537:1']['resolved'], '\n')




 