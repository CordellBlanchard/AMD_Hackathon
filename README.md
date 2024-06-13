# AMD_Hackathon Challenge # 3

## Configuration

Before running the application, you need to set up your GitHub API access token to allow the application to fetch data from GitHub.

1. Generate a new GitHub API access token:
    - Visit [GitHub's Tokens Page](https://github.com/settings/tokens) and generate a new token with the appropriate permissions. For this project, you will need permissions to access repositories.

2. Configure your access token in the application:
    - Open the `blame_api.py` file located in the project directory under `backend/app/util`.
    - Find the line that contains `TOKEN = 'your_access_token_here'`.
    - Replace `'your_access_token_here'` with your actual GitHub API access token.

Please ensure that you include all necessary permissions for the token to avoid any access issues. This token will be used to authenticate and interact with GitHub's API securely.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Python 3.8+
- pip
- Docker and Docker Compose
- A GitHub account

### How to run

1. Clone the repository:

    `git clone https://github.com/CordellBlanchard/AMD_Hackathon.git`

2. Navigate to the project directory:

    `cd AMD_Hackathon`

3. Build and start the Docker containers:

    `docker-compose up --build`

    note: this may be need to run again if it doesnt work the first time!

4. Access the UI through  http://localhost