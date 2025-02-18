from app import db

# Many-to-many relationship between Issue and Blame
issue_blame = db.Table('issue_blame',
    db.Column('issue_id', db.String, db.ForeignKey('issue.id'), primary_key=True),
    db.Column('blame_id', db.Integer, db.ForeignKey('blame.id'), primary_key=True), 
)

issue_rule = db.Table('issue_rule',
    db.Column('issue_id', db.String, db.ForeignKey('issue.id'), primary_key=True),
    db.Column('rule_id', db.String, db.ForeignKey('rule.id'), primary_key=True)
)

class Issue(db.Model):
    id = db.Column(db.String, primary_key=True)  # Changed from Integer to String to accommodate the hash
    description = db.Column(db.Text, nullable=True)
    files = db.Column(db.PickleType, nullable=True)  # List of files
    lines = db.Column(db.PickleType, nullable=True)  # List of lines
    start_columns = db.Column(db.PickleType, nullable=True)  # List of start columns
    end_columns = db.Column(db.PickleType, nullable=True)  # List of end columns
    # rule_id = db.Column(db.String, db.ForeignKey('rule.id'), nullable=True)  # Foreign key to Rule
    # rule = db.Column(db.String, nullable=True)  # Rule ID
    commit = db.Column(db.String, nullable=True)  # Commit hash
    date = db.Column(db.DateTime, nullable=True)  # Date of the committ
    resolved = db.Column(db.Boolean, default=False)  # Whether the issue is resolved or not
    blames = db.relationship('Blame', secondary=issue_blame, backref=db.backref('issues', lazy=True))
    rule = db.relationship('Rule', secondary=issue_rule, backref=db.backref('issues', lazy=True))

    def serialize(self):
        return {
            'id': self.id,
            'description': self.description,
            'files': self.files,
            'lines': self.lines,
            'start_columns': self.start_columns,
            'end_columns': self.end_columns,
            'rule': self.rule,
            'commit': self.commit,
            'date': self.date,
            'resolved': self.resolved,
            'blames': [blame.serialize() for blame in self.blames], 
            'rule': [rule.serialize() for rule in self.rule],
        }

class Blame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    commit_oid = db.Column(db.String, nullable=False)  # Commit OID
    author_name = db.Column(db.String, nullable=False)  # Author's name
    author_email = db.Column(db.String, nullable=False)  # Author's email
    authored_date = db.Column(db.DateTime, nullable=False)  # Authored date
    authored_by_committer = db.Column(db.Boolean, default=False)  # Whether authored by committer
    starting_line = db.Column(db.Integer, nullable=False)  # Starting line of the blame
    ending_line = db.Column(db.Integer, nullable=False)  # Ending line of the blame
    line_content = db.Column(db.String, nullable=False)  # Content of the line
    file = db.Column(db.String, nullable=False)  # File name

    def serialize(self):
        return {
            'id': self.id,
            'commit_oid': self.commit_oid,
            'author_name': self.author_name,
            'author_email': self.author_email,
            'authored_date': self.authored_date,
            'authored_by_committer': self.authored_by_committer,
            'starting_line': self.starting_line,
            'ending_line': self.ending_line,
            'line_content': self.line_content,
            'file': self.file
        }

class Rule(db.Model): 
    """
    Represents a rule in the system.

    Attributes:
        id (str): The unique identifier of the rule.
        name (str): The name of the rule.
        shortDescription (str): A shorter description of the rule.
        fullDescription (str): The complete description of the rule.
        enabled (str): Indicates whether the rule is enabled or not.
        level (str): The level of the rule.
        tags (list): The tags associated with the rule.
        kind (str): The kind of the rule.
        precision (str): The precision of the rule.
        security_severity (str): The security severity of the rule.
        sub_severity (str): The sub severity of the rule.
    """

    id = db.Column(db.String, primary_key=True) # Changed from Integer to String to accommodate the hash
    name = db.Column(db.String, nullable=False) # Rule name
    shortDescription = db.Column(db.String, nullable=False) # Shorter description of rule 
    fullDescription = db.Column(db.String, nullable=False) # Complete description of rule 
    enabled = db.Column(db.String, nullable=False) # Whether the rule is enabled or not
    level = db.Column(db.String, nullable=True) # Level of the rule
    tags = db.Column(db.PickleType, nullable=False) # Tags associated with the rule
    kind = db.Column(db.String, nullable=False) # Kind of the rule
    precision = db.Column(db.String, nullable=True) # Precision of the rule
    security_severity = db.Column(db.String, nullable=True) # Security severity of the rule
    sub_severity = db.Column(db.String, nullable=True) # Sub severity of the rule 

    def serialize(self):
        """
        Serializes the rule object into a dictionary.

        Returns:
            dict: A dictionary representation of the rule object.
        """
        return {
            'id': self.id,
            'name': self.name,
            'shortDescription': self.shortDescription,
            'fullDescription': self.fullDescription,
            'enabled': self.enabled,
            'level': self.level,
            'tags': self.tags,
            'kind': self.kind,
            'precision': self.precision,
            'security-severity': self.security_severity,
            'sub-severity': self.sub_severity
        }
    
class LLMCache(db.Model):
    """
    Represents a LLMCache object.

    Attributes:
        id (int): The unique identifier for the LLMCache.
        suggestion (str): The suggestion associated with the LLMCache.
        blame_id (int): The foreign key referencing the associated Blame object.
        blame (Blame): The associated Blame object.

    Methods:
        serialize(): Serializes the LLMCache object into a dictionary.

    """

    id = db.Column(db.Integer, primary_key=True)
    suggestion = db.Column(db.Text, nullable=False)
    blame_id = db.Column(db.Integer, db.ForeignKey('blame.id'), nullable=False)
    blame = db.relationship('Blame', backref=db.backref('llm_caches', lazy=True))

    def serialize(self):
        """
        Serializes the LLMCache object into a dictionary.

        Returns:
            dict: A dictionary representation of the LLMCache object.

        """
        return {
            'id': self.id,
            'blame_id': self.blame_id,
            'suggestion': self.suggestion,
            'blame': self.blame.serialize() if self.blame else None
        }


class SarifFile(db.Model):  
    """
    Represents a SARIF file in the database.

    Attributes:
        id (int): The unique identifier for the SARIF file.
        sarif_file (str): The path or name of the SARIF file.
        date (datetime): The date when the SARIF file was created.

    Methods:
        serialize: Returns a dictionary representation of the SARIF file object.
    """
    id = db.Column(db.Integer, primary_key=True)  
    sarif_file = db.Column(db.String)  
    date = db.Column(db.DateTime)

    def serialize(self):
        """
        Returns a dictionary representation of the SARIF file object.

        Returns:
            dict: A dictionary containing the serialized SARIF file data.
        """
        return {
            'id': self.id,
            'sarif_file': self.sarif_file
        } 
    
    def __repr__(self):
        return f'<SarifData {self.sarif_file}>'