import psycopg2 
from sarif_parser import get_updated_state


if __name__ == "__main__": 

    conn = psycopg2.connect(database = "GitNarc", 
                        user = "amd", 
                        host= 'localhost',
                        password = "amd" 
                        ) 
    
    print("Connected to database successfully") 

    # Get the latest SARIF file information
    
    sarif_file_name = '../database-d25dd807485c-2020-01-03.sarif'
    old_sarif_file_name = '../database-b8b8ebcf851d-2017-04-11.sarif'

    latest_dict = get_updated_state(old_sarif_file_name, sarif_file_name)  


    # Set up database operations 
    cursor = conn.cursor() 

    # Create table CommitHashes 
    cursor.execute('''CREATE TABLE IF NOT EXISTS CommitHashes 
                    (commit_id PRIMARY KEY,  
                    commit_date DATE NOT NULL)''')
    
    # Insert data into CommitHashes 

    for commit_id, commit_info in latest_dict.items(): 
        commit_date = commit_info['date']
        cursor.execute("INSERT INTO CommitHashes (commit_id, commit_date) VALUES (%s, %s) ON CONFLICT (commit_id) DO NOTHING", 
                       (commit_id, commit_date)) 
        

    # Create table dynamically based on the dictionary keys
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS SarifData (
            commit_id VARCHAR PRIMARY KEY,
            files TEXT[],
            lines INTEGER[],
            start_columns INTEGER[],
            end_columns INTEGER[],
            rule VARCHAR,
            description TEXT,
            commit VARCHAR,
            date DATE,
            resolved BOOLEAN
        )
    ''')

    # Insert data into the table
    for commit_id, commit_info in latest_dict.items():
        cursor.execute(f'''
            INSERT INTO SarifData (
                commit_id, files, lines, start_columns, end_columns,
                rule, description, commit, date, resolved
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            ) ON CONFLICT (commit_id) DO NOTHING
        ''', (
            commit_id, 
            commit_info['files'], 
            commit_info['lines'], 
            commit_info['start_columns'], 
            commit_info['end_columns'], 
            commit_info['rule'], 
            commit_info['description'], 
            commit_info['commit'], 
            commit_info['date'], 
            commit_info['resolved']
        ))
    
    cur = conn.cursor()
    cur.execute('SELECT * FROM CommitHashes;')
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    print("connection closed")

    for row in rows:
        print(row)
