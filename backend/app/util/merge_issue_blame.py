from app import db
from app.util.blame_api import getFullHashFromPartial

from app.models.models import Issue, Blame, Rule
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
            issue.date = new_dict[issue.id]['datSe']
            issue.resolved = new_dict[issue.id]['resolved']
            # Remove the issue from the new_dict
            new_dict.pop(issue.id)

    # Commit the changes to the database
    db.session.commit()
  
def resolve_rules(rules_broken):
    # Get all rules from the database
    rules = Rule.query.all()

    for rule in rules:
        # if rule id is in the rules_broken, update rule information
        if rules_broken.get(rule.id) is not None:
            # If the rule id is in the rules_broken, update the rule with the new information
            rule.name = rules_broken[rule.id]['name']
            rule.shortDescription = rules_broken[rule.id]['shortDescription']['text']
            rule.fullDescription = rules_broken[rule.id]['fullDescription']['text']
            rule.enabled = rules_broken[rule.id]['defaultConfiguratrion']['enabled']
            rule.level = rules_broken[rule.id]['defaultConfiguration']['level']
            rule.tags = rules_broken[rule.id]['properties']['tags']
            rule.kind = rules_broken[rule.id]['properties']['kind']
            rule.precision = rules_broken[rule.id]['properties']['precision']
            rule.security_severity = rules_broken[rule.id]['properties']['securitySeverity']
            rule.sub_severity = rules_broken[rule.id]['properties']['subSeverity']

            # Remove the rule from the rules_broken
            rules_broken.pop(rule.id)

    # Commit the changes to the database
    db.session.commit()

    # Add the remaining rules to the database
    for rule_id in rules_broken:
        rule = Rule(id=rule_id, name=rules_broken[rule_id]['name'], short_description=rules_broken[rule_id]['short_description'], 
                    full_description=rules_broken[rule_id]['full_description'], resolved=False)
        db.session.add(rule)
    db.session.commit()

def merge_sarif(sarif_file_name):  
    # pase the sarif file
    new_dict, rules_broken = parse_sarif_file(sarif_file_name) 

    # get repo
    repo = Repo("tensorflow", "tensorflow") # this can also come from the something else (owner, repo_name)  

    # resolve old issues
    resolve_issues(new_dict)
    resolve_rules(rules_broken) 

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

    # Add remaining broken rules that were not present in database 
    for key in rules_broken.keys():
        # If the rule id is in the rules_broken, update the rule with the new information
        rule = Rule(id=key, name=rules_broken[key]['name'], shortDescription=rules_broken[key]['shortDescription'], 
                    fullDescription=rules_broken[key]['fullDescription'], enabled=rules_broken[key]['defaultConfiguration']['enabled'],
                    level=rules_broken[key]['defaultConfiguration']['level'], tags=rules_broken[key]['properties']['tags'],
                    kind=rules_broken[key]['properties']['kind'], precision=rules_broken[key]['properties']['precision'],
                        security_severity=rules_broken[key]['properties']['securitySeverity'], sub_severity=rules_broken[key]['properties']['subSeverity'])
        db.session.add(rule)
    db.session.commit()
