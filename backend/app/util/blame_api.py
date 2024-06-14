import requests
from concurrent.futures import ThreadPoolExecutor

# Your personal access token
TOKEN = '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'

# The GraphQL endpoint
URL = 'https://api.github.com/graphql'

def getLine(repo, commit_hash, file_path, line_number):
    url = f"https://api.github.com/repos/{repo.owner}/{repo.name}/contents/{file_path}"
    headers = {
        "Accept": "application/vnd.github.v3.raw",
        "Authorization": f"token {TOKEN}"  # If authentication is required
    }
    params = {
        "ref": commit_hash
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        content = response.text
        lines = content.split('\n')
        if line_number <= len(lines):
            return lines[line_number - 1]
        else:
            return None
    else:
        print(f"Error: {response.status_code}")
        return None
    
def getFullHashFromPartial(repo, partial_hash):
    url = f"https://api.github.com/repos/{repo.owner}/{repo.name}/commits/{partial_hash}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {TOKEN}"  # If authentication is required
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()['sha']
    else:
        print(f"Error: {response.status_code}")
        return None
    

def getBlame(repo, commit_hash, file_path, line_number):
    query = f"""
    {{
    repository(name: "{repo.name}", owner: "{repo.owner}") {{
        # branch name
        object(oid:"{commit_hash}") {{      
            ... on Commit {{
            # full repo-relative path to blame file
            blame(path:"{file_path}") {{
                ranges {{
                commit {{
                    oid
                    author {{
                        name
                        email
                    }}
                    authoredDate
                    authoredByCommitter 
                }}
                startingLine
                endingLine
                }}
            }}
            }}
        }}
        }}
    }}
    """

    # Headers for the request
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }

    # Convert the query to a JSON object
    payload = {
        'query': query
    }

    # Make the request
    response = requests.post(URL, json=payload, headers=headers)

    # Check for errors
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        try:
            lines = data["data"]["repository"]["object"]["blame"]["ranges"]

            for line in lines:
                if line["startingLine"] <= line_number <= line["endingLine"]:
                    return line
        except KeyError:
            print(data)
    else:
        print(f"Query failed to run by returning code of {response.status_code}. {response.text}")


class Repo():
    def __init__(self, owner, name) -> None:
        self.owner = owner
        self.name = name

def getLineInfo(repo, commit_hash, file_path, line_number):
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_blame = executor.submit(getBlame, repo, commit_hash, file_path, line_number)
        future_line_content = executor.submit(getLine, repo, commit_hash, file_path, line_number)

    blame = future_blame.result()
    line_content = future_line_content.result()

    return blame, line_content

if __name__ == "__main__":
    repo = Repo("tensorflow", "tensorflow")
    blame, line_content = getLineInfo(repo, "5a7786812dd4cb4511e8ef85b12017cf3d2ae08d", "tensorflow/python/keras/utils/data_utils.py", 135)
    print(blame)
    print(blame['startingLine'])
    print(line_content)