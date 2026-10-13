import psycopg2
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Connections
# Supabase (Old)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
# Neon (New)
neon_conn = psycopg2.connect(os.getenv("NEON_CONNECTION_STRING"))

def migrate():
    print("🚀 Fetching data from Supabase...")
    
    # We add .limit(10000) just to be sure, though default might be lower
    # We also check the data property correctly
    response = supabase.table("screening_phase_1").select("*").range(0, 9999).execute()
    data = response.data
    
    if not data:
        print("❌ Supabase returned no data. Check your connection or table name.")
        # Debugging: print what we actually got
        print(f"Response: {response}")
        return
    
    print(f"📦 Found {len(data)} records. Inserting into Neon...")
    
    cursor = neon_conn.cursor()
    # Using execute_values is much faster for bulk inserts than a loop
    from psycopg2.extras import execute_values
    
    insert_query = """
    INSERT INTO public.screening_phase_1 
    (id, created_at, q1_score, q2_score, q3_score, q4_score, q5_score, total_score, title, doi, abstract_text, source_database, decision, exclusion_reason)
    VALUES %s
    ON CONFLICT (id) DO NOTHING;
    """
    
    # Convert list of dicts to list of tuples
    tuples = [
        (
            row.get('id'), row.get('created_at'), row.get('q1_score'), row.get('q2_score'),
            row.get('q3_score'), row.get('q4_score'), row.get('q5_score'), row.get('total_score'),
            row.get('title'), row.get('doi'), row.get('abstract_text'), row.get('source_database'),
            row.get('decision'), row.get('exclusion_reason')
        ) for row in data
    ]
    
    execute_values(cursor, insert_query, tuples)
    neon_conn.commit()
    cursor.close()
    print("✅ Migration complete!")
    
if __name__ == "__main__":
    migrate()