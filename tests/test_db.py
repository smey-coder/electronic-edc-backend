from sqlalchemy import text
from app.database.session import engine

def test_mysql_connection():
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT VERSION()")).scalar()
            db_name = conn.execute(text("SELECT DATABASE()")).scalar()
            print("Connection Success!")
            print(f"Database: {db_name}")
            print(f"MySQL Version: {version}")
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    test_mysql_connection()