from app import db
from app.util.blame_api import getFullHashFromPartial

from app.models.models import Issue, Blame
from app.util.sarif_parser import parse_sarif_file 
from app.util.blame_api import Repo, getLineInfo    

def resolve_issues(new_dict):
    # Get all unresolved issues from the database
    unresolved_issues = Issue.query.filter_by(resolved=False).all()

    for issue in unresolved_issues:
        # If the issue id is in the new_dict, set it to resolved
        if new_dict.get(issue.id) is None:
            issue.resolved = True
        else: 
            # If the issue id is in the new_dict, update the issue with the new information
            issue.description = new_dict[issue.id]['description']
            issue.files = new_dict[issue.id]['files']
            issue.lines = new_dict[issue.id]['lines']
            issue.start_columns = new_dict[issue.id]['start_columns']
            issue.end_columns = new_dict[issue.id]['end_columns']
            issue.rule = new_dict[issue.id]['rule']
            issue.commit = new_dict[issue.id]['commit']
            issue.date = new_dict[issue.id]['date']
            issue.resolved = new_dict[issue.id]['resolved']
            # Remove the issue from the new_dict
            new_dict.pop(issue.id)

    # Commit the changes to the database
    db.session.commit()
  
def merge_sarif(sarif_file_name):  
    # pase the sarif file
    new_dict = parse_sarif_file(sarif_file_name) 

    # get repo
    repo = Repo("tensorflow", "tensorflow") # this can also come from the something else (owner, repo_name)  

    # resolve old issues
    resolve_issues(new_dict)

    # go through each issue in the dictionary and get the blame information
    for key in new_dict:  
        partial_hash = new_dict[key]['commit']
        commit_hash = getFullHashFromPartial(repo, partial_hash)
        issue = Issue(id=key, description=new_dict[key]['description'], files=new_dict[key]['files'], lines=new_dict[key]['lines'],
                      start_columns=new_dict[key]['start_columns'], end_columns=new_dict[key]['end_columns'], rule=new_dict[key]['rule'],
                      commit=commit_hash, date=new_dict[key]['date'], resolved=new_dict[key]['resolved']) 
        # go through each file corresponding to current issue and get blame information
        for file, line_number in zip(new_dict[key]['files'], new_dict[key]['lines']): 
            blame_info, line_content = getLineInfo(repo, commit_hash, file, line_number)
            blame = Blame(commit_oid=blame_info['commit']['oid'], author_name=blame_info['commit']['author']['name'], 
                          author_email=blame_info['commit']['author']['email'], authored_date=blame_info['commit']['authoredDate'],
                          authored_by_committer=blame_info['commit']['authoredByCommitter'], starting_line=blame_info['startingLine'], 
                          ending_line=blame_info['endingLine'], line_content=line_content, file=file)  
            issue.blames.append(blame)
        db.session.add(issue)
    db.session.commit()
