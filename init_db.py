import mysql.connector
from mysql.connector import Error
import os

def init_db():
    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1321334050'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS gym_db")
            cursor.execute("USE gym_db")
            
            # Read and execute SQL file
            with open('gym_db.sql', 'r') as sql_file:
                # Read the entire SQL file
                sql_script = sql_file.read()
                # Split into individual statements but preserve delimiter changes
                statements = sql_script.split(';')
                
                # Execute each statement
                for statement in statements:
                    # Skip empty statements
                    if statement.strip():
                        cursor.execute(statement)
                        connection.commit()
            
            print("Database initialized successfully!")
            
    except Error as e:
        print(f"Error initializing database: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed.")

if __name__ == "__main__":
    init_db()