from flask import Blueprint, request, jsonify
from sqlalchemy import or_, func

from app import db
#from app.models.models import User
from app.models.models import Issue, Blame, issue_blame, LLMCache, issue_rule, Rule
from datetime import datetime 
from collections import defaultdict
from app.util.llm import get_llm_response, create_cache 

main_bp = Blueprint('main', __name__)

# IMPORTANT : leave the root route to the Elastic Beanstalk Load Balancer health check, it performs a GET to '/' every 5 seconds and expects a '200'
@main_bp.route('/', methods=['GET'])
def EB_healthcheck():
    """
    Endpoint for performing a health check of the application.

    Returns:
        str: A string indicating the health status of the application.
    """
    return 'OK', 200
    

@main_bp.route('/group_issues', methods=['GET'])
def group_issues():
    """
    Group issues based on the specified criteria and return the grouped results as JSON.

    Returns:
        A JSON response containing the grouped issues.

    Raises:
        Exception: If an error occurs during the grouping process.
    """
    try:
        # Get query parameters
        group_by = request.args.get('group_by')

        # Start with all Issues
        #query = db.session.query(Issue, Blame).select_from(Issue).join(issue_blame).join(Blame)
        query = db.session.query(Issue, Blame, Rule).select_from(Issue).join(issue_blame).join(Blame).join(issue_rule).join(Rule)

        if group_by:
            if group_by == 'id':
                # Group by issue id
                query = query.order_by(Issue.id)
            elif group_by == 'rule':
                # Group by rule id
                query = query.order_by(getattr(Rule, 'id'))
            elif group_by in ['file', 'author_name']:
                # Group by blame file or author name
                query = query.order_by(getattr(Blame, group_by))
        
        # Execute the query
        issue_blame_pairs = query.all()

        # Group the results
        grouped_issues = defaultdict(list)
        for issue, blame, rule in issue_blame_pairs:
            if group_by == 'rule':
                key = rule.id
            else:
                key = getattr(issue if group_by == 'id' else blame, group_by)
            grouped_issues[key].append(issue.serialize())

        return jsonify(grouped_issues)
    except Exception as e:
        db.session.rollback()
        return f'An error occurred: {str(e)}', 500

@main_bp.route('/list', methods=['GET'])
def list_users():
    """
    Retrieve a list of all issues.

    Returns:
        A JSON response containing a list of serialized user objects.
        If an error occurs, a string with the error message and a 500 status code.
    """
    try:
        issues = db.session.query(Issue).all()
        # calling the __str__ representation defined in the User model 
        return jsonify([i.serialize() for i in issues])
    except Exception as e:
        db.session.rollback()
        return f'An error occurred: {str(e)}', 500
    
@main_bp.route('/llm_cache', methods=['GET'])
def view_cache():
    try:
        cache = db.session.query(LLMCache).all()
        # calling the __str__ representation defined in the User model 
        return jsonify([i.serialize() for i in cache])
    
    except Exception as e:
        db.session.rollback()
        return f'An error occurred: {str(e)}', 500

@main_bp.route('/generate_llm_response', methods=['POST'])
def generate_llm_response():
    """
    Generate LLM response based on the provided parameters and cache it.

    Returns:
        A JSON response containing a success message and the generated LLM response.

    Raises:
        Exception: If an error occurs during the process.
    """
    data = request.get_json()

    # Extract required parameters from the request
    rule_info = data.get("rule_info")
    issue_message = data.get("issue_message")
    file = data.get("file")
    line = data.get("line")
    commit_hash = data.get("commit_hash")
    blame_id = data.get("blame_id")

    # Check if all required parameters are provided
    if not all([rule_info, issue_message, file, line, commit_hash, blame_id]):
        return jsonify({"error": "Missing required parameters"}), 400

    # Use the helper function
    result, status_code = handle_llm_response(rule_info, issue_message, file, line, commit_hash, blame_id)
    return jsonify(result), status_code


def handle_llm_response(rule_info, issue_message, file, line, commit_hash, blame_id):
    try:
        llm_response = 0
        # Generate the LLM response
        response = get_llm_response(rule_info, issue_message, file, line, commit_hash)

        # Create cache entry
        create_cache(blame_id, response)

        return {"message": "LLM response generated and cached successfully", "response": response}, 200

    except Exception as e:
        db.session.rollback()
        return {"error ": f'An error occurred: {str(e)}'}, 500


@main_bp.route('/test_llm', methods=['GET'])
def test_llm():
    """
    Retrieve and serialize an issue by ID, along with its associated blame data.

    Args:
        id (int): The ID of the issue to retrieve.

    Returns:
        A JSON response containing the serialized issue data and associated blame data.
        If the issue is not found, a JSON response with an error message and status code 404 is returned.
        If an error occurs during the retrieval process, a string with the error message and status code 500 is returned.
    """
    try:
        id = '3680e0d6cadd14ee:1' 
        # Retrieve the specific issue by ID
        issue = Issue.query.get(id)
        if not issue:
            return jsonify({"error": "Issue not found"}), 404

        # Serialize the issue data
        issue_data = issue.serialize() 

        print('CHECK THIS:', issue.rule)

        # Access the first blame associated with the issue
        first_blame = issue.blames[0] if issue.blames else None
        commit_hash = issue.commit 
        issue_message =  issue.description
        blame_id = issue.blames[0].id
        file = issue.blames[0].file
        line =  issue.blames[0].starting_line
        rule_info = issue.rule[0].fullDescription

        # Use the helper function
        result, status_code = handle_llm_response(rule_info, issue_message, file, line, commit_hash, blame_id)
        return jsonify(result), status_code

    except Exception as e:
        db.session.rollback()
        return f'An error occurred: {str(e)}', 500
    

    
    # Create endpoint to retrieve rule information
@main_bp.route('/rules', methods=['GET'])
def list_rules():
    try:
        rules = db.session.query(Rule).all()
        return jsonify([r.serialize() for r in rules])
    except Exception as e:
        db.session.rollback()
        return f'An error occurred: {str(e)}', 500    
    
# Query the database for a specific rule 
@main_bp.route('/rule/<rule_id>', methods=['GET'])
def get_rule(rule_id):
    try:
        rule = db.session.query(Rule).filter_by(id=rule_id).all()
        return jsonify(rule.serialize())
    except Exception as e:
        db.session.rollback()