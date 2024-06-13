from app import db

# Many-to-many relationship between Issue and Blame
issue_blame = db.Table('issue_blame',
    db.Column('issue_id', db.Integer, db.ForeignKey('issue.id'), primary_key=True),
    db.Column('blame_id', db.Integer, db.ForeignKey('blame.id'), primary_key=True)
)

class Issue(db.Model):
    id = db.Column(db.String, primary_key=True)  # Changed from Integer to String to accommodate the hash
    description = db.Column(db.Text, nullable=True)
    files = db.Column(db.PickleType, nullable=True)  # List of files
    lines = db.Column(db.PickleType, nullable=True)  # List of lines
    start_columns = db.Column(db.PickleType, nullable=True)  # List of start columns
    end_columns = db.Column(db.PickleType, nullable=True)  # List of end columns
    rule = db.Column(db.String, nullable=True)  # Rule ID
    commit = db.Column(db.String, nullable=True)  # Commit hash
    date = db.Column(db.DateTime, nullable=True)  # Date of the committ
    resolved = db.Column(db.Boolean, default=False)  # Whether the issue is resolved or not
    blames = db.relationship('Blame', secondary=issue_blame, backref=db.backref('issues', lazy=True))

    def __repr__(self):
        return f'<Issue {self.title}>'

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


    def __repr__(self):
        return f'<Blame {self.name}>'
    

class SarifFile(db.Model):  
    id = db.Column(db.Integer, primary_key=True)  
    sarif_file = db.Column(db.String)  

    def serialize(self):
        return {
            'id': self.id,
            'sarif_file': self.sarif_file
        } 
    
    def __repr__(self):
        return f'<SarifData {self.sarif_file}>'