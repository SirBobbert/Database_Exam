import os
import pyodbc
from dotenv import load_dotenv
from flask import Flask, request, jsonify

app = Flask(__name__)

load_dotenv()
db_pw = os.getenv("MSSQL_PW")

# Endpoint for executing the stored procedure
@app.route('/api/getUsers', methods=['POST'])
def execute_stored_procedure():
    # Parse the request data
    user_id = request.get_json('user_id')

    # Establish a connection to the SQL Server database
    conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost;'
    'PORT=1433;'
    'DATABASE=DBExam;'
    'UID=sa;'
    'PWD=' + db_pw + ';'
)

    # Create a cursor object to execute SQL statements
    cursor = conn.cursor()

    try:
        # Execute the stored procedure
        cursor.execute("{CALL GetUsers(?)}", user_id)

        # Fetch the result set
        result_set = cursor.fetchall()

        # Process the result set
        users = []
        for row in result_set:
            user = {
                'user_id': row.UserID,
                'username': row.UserName,
                'email': row.Email,
                'address': row.Address
            }
            users.append(user)

        # Commit the transaction
        conn.commit()

        # Return the response as JSON
        return jsonify(users)

    except Exception as e:
        # Rollback the transaction in case of any error
        conn.rollback()
        # Optionally, handle the exception and return an error response

    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run()
