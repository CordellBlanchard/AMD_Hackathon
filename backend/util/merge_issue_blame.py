from app import db

from AMD_Hackathon.backend.models.models import Issue, Blame
from AMD_Hackathon.backend.util.sarif_parser import parse_sarif_file 
from AMD_Hackathon.backend.util.blame_api import Repo, getLineInfo    

def resolve_issues(new_dict):
    # Get all unresolved issues from the database
    unresolved_issues = Issue.query.filter_by(resolved=False).all()

    for issue in unresolved_issues:
        # If the issue id is in the new_dict, set it to resolved
        if new_dict.get(issue.id) is not None:
            issue.resolved = True

    # Commit the changes to the database
    db.session.commit()
  
def merge_sarif(sarif_file_name):  
    # pase the sarif file
    new_dict = parse_sarif_file(sarif_file_name) 

    # get repo
    repo = Repo("tensorflow", "tensorflow") # this can also come from the something else (owner, repo_name)  

    # go through each issue in the dictionary and get the blame information
    for key in new_dict:  
        commit_hash = new_dict[key]['commit'] 
        issue = Issue(id=key, description=new_dict[key]['description'], files=new_dict[key]['files'], lines=new_dict[key]['lines'],
                      start_columns=new_dict[key]['start_columns'], end_columns=new_dict[key]['end_columns'], rule=new_dict[key]['rule'],
                      commit=commit_hash, date=new_dict[key]['date'], resolved=new_dict[key]['resolved']) 
        # go through each file corresponding to current issue and get blame information
        for file, line_number in zip(new_dict[key]['files'], new_dict[key]['lines']):  
            blame_info, line_content = getLineInfo(repo, commit_hash, file, line_number)
            blame = Blame(commit_oid=blame_info['commit']['oid'], author_name=blame_info['commit']['author']['name'], 
                          author_email=blame_info['commit']['author']['email'], authored_date=blame_info['commit']['authored_date'],
                          authored_by_committer=blame_info['authored_by_committer'], starting_line=blame_info['starting_line'], 
                          ending_line=blame_info['endingLine'], line_content=line_content, file=file)  
            issue.blames.append(blame)
        db.session.add(issue)
    db.session.commit()

    # resolve old issues
    resolve_issues(new_dict)
