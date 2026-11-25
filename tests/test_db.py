
from app.database.session import engine

try:
    with engine.connect() as connection:
        result = connection.exec_driver_sql("SELECT VERSION()")
        print("Database connected successfully!")
        print("MySQL Version:", result.scalar())

except Exception as e:
    print("Database connection failed!")
    print("Error:", e)
