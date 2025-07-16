from sqlalchemy import create_engine, MetaData, text

# Connect to the database
DATABASE_URL = 'sqlite:///elements.db'
engine = create_engine(DATABASE_URL)

# Reflect existing schema
metadata = MetaData()
metadata.reflect(bind=engine)

# Open a connection and transaction
with engine.connect() as conn:
    trans = conn.begin()
    try:
        # Disable foreign key constraints (SQLite)
        conn.execute(text("PRAGMA foreign_keys = OFF;"))

        # Delete all rows from all tables
        for table in reversed(metadata.sorted_tables):
            conn.execute(table.delete())

        # Re-enable foreign key constraints
        conn.execute(text("PRAGMA foreign_keys = ON;"))
        trans.commit()
        print("✅ All rows deleted from all tables.")
    except Exception as e:
        trans.rollback()
        print(f"❌ Error during deletion: {e}")
