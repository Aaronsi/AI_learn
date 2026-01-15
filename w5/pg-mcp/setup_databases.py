"""Setup script to create and load test databases from fixtures"""

import asyncio
import asyncpg
from pathlib import Path

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "postgres",
}

# Database names and their corresponding SQL files
DATABASES = {
    "pg_mcp_small": "fixtures/small.sql",
    "pg_mcp_medium": "fixtures/medium.sql",
    "pg_mcp_large": "fixtures/large.sql",
}


async def create_database(db_name: str) -> None:
    """Create a database if it doesn't exist"""
    # Connect to postgres database to create new database
    try:
        conn = await asyncpg.connect(
            database="postgres",
            **DB_CONFIG
        )
    except Exception as e:
        print(f"\n✗ Cannot connect to PostgreSQL server!")
        print(f"  Error: {e}")
        print(f"\nPlease ensure:")
        print(f"  1. PostgreSQL service is running")
        print(f"  2. Connection settings are correct (host={DB_CONFIG['host']}, port={DB_CONFIG['port']})")
        print(f"  3. User '{DB_CONFIG['user']}' has permission to create databases")
        print(f"\nTo start PostgreSQL service on Windows:")
        print(f"  Start-Service -Name 'postgresql-x64-17'")
        print(f"  Or use Services.msc to start 'postgresql-x64-17 - PostgreSQL Server 17'")
        raise
    try:
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if exists:
            print(f"Database {db_name} already exists, dropping it...")
            # Terminate all connections to the database
            await conn.execute(
                f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = $1
                AND pid <> pg_backend_pid()
                """,
                db_name
            )
            await conn.execute(f'DROP DATABASE "{db_name}"')
        
        # Create database
        await conn.execute(f'CREATE DATABASE "{db_name}"')
        print(f"✓ Created database: {db_name}")
    finally:
        await conn.close()


async def load_sql_file(db_name: str, sql_file: Path) -> None:
    """Load SQL file into database"""
    print(f"Loading {sql_file} into {db_name}...")
    
    # Read SQL file
    sql_content = sql_file.read_text(encoding="utf-8")
    
    # Connect to the target database
    conn = await asyncpg.connect(
        database=db_name,
        **DB_CONFIG
    )
    try:
        # Execute SQL script
        await conn.execute(sql_content)
        print(f"✓ Loaded {sql_file.name} into {db_name}")
    finally:
        await conn.close()


async def test_database(db_name: str) -> None:
    """Test database connection and basic queries"""
    print(f"\nTesting {db_name}...")
    
    conn = await asyncpg.connect(
        database=db_name,
        **DB_CONFIG
    )
    try:
        # Test 1: Check connection
        version = await conn.fetchval("SELECT version()")
        print(f"  ✓ Connected to PostgreSQL: {version.split(',')[0]}")
        
        # Test 2: List tables
        tables = await conn.fetch(
            """
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
            """
        )
        table_names = [row["tablename"] for row in tables]
        print(f"  ✓ Found {len(table_names)} tables: {', '.join(table_names)}")
        
        # Test 3: Count rows in each table
        for table_name in table_names:
            count = await conn.fetchval(f'SELECT COUNT(*) FROM "{table_name}"')
            print(f"    - {table_name}: {count} rows")
        
        # Test 4: List views
        views = await conn.fetch(
            """
            SELECT viewname 
            FROM pg_views 
            WHERE schemaname = 'public'
            ORDER BY viewname
            """
        )
        if views:
            view_names = [row["viewname"] for row in views]
            print(f"  ✓ Found {len(view_names)} views: {', '.join(view_names)}")
        
        print(f"  ✓ {db_name} is ready and working!")
        
    finally:
        await conn.close()


async def check_postgresql_connection() -> bool:
    """Check if PostgreSQL server is accessible"""
    try:
        conn = await asyncpg.connect(
            database="postgres",
            **DB_CONFIG
        )
        await conn.close()
        return True
    except Exception:
        return False


async def main():
    """Main function to setup all databases"""
    print("=" * 60)
    print("PostgreSQL Database Setup Script")
    print("=" * 60)
    
    # Check PostgreSQL connection first
    print("\n[Checking PostgreSQL connection...]")
    if not await check_postgresql_connection():
        print("\n✗ Cannot connect to PostgreSQL server!")
        print(f"\nConnection settings:")
        print(f"  Host: {DB_CONFIG['host']}")
        print(f"  Port: {DB_CONFIG['port']}")
        print(f"  User: {DB_CONFIG['user']}")
        print(f"\nPlease ensure:")
        print(f"  1. PostgreSQL service is running")
        print(f"  2. Connection settings are correct")
        print(f"  3. User '{DB_CONFIG['user']}' has permission to create databases")
        print(f"\nTo start PostgreSQL service on Windows:")
        print(f"  Option 1: Start-Service -Name 'postgresql-x64-17' (requires admin)")
        print(f"  Option 2: Open Services.msc and start 'postgresql-x64-17 - PostgreSQL Server 17'")
        print(f"  Option 3: net start postgresql-x64-17 (requires admin)")
        return
    
    print("✓ PostgreSQL server is accessible")
    
    base_path = Path(__file__).parent
    
    # Step 1: Create databases
    print("\n[Step 1] Creating databases...")
    for db_name in DATABASES.keys():
        try:
            await create_database(db_name)
        except Exception as e:
            print(f"✗ Error creating {db_name}: {e}")
            return
    
    # Step 2: Load SQL files
    print("\n[Step 2] Loading SQL files...")
    for db_name, sql_file_rel in DATABASES.items():
        sql_file = base_path / sql_file_rel
        if not sql_file.exists():
            print(f"✗ SQL file not found: {sql_file}")
            return
        try:
            await load_sql_file(db_name, sql_file)
        except Exception as e:
            print(f"✗ Error loading {sql_file_rel} into {db_name}: {e}")
            import traceback
            traceback.print_exc()
            return
    
    # Step 3: Test databases
    print("\n[Step 3] Testing databases...")
    for db_name in DATABASES.keys():
        try:
            await test_database(db_name)
        except Exception as e:
            print(f"✗ Error testing {db_name}: {e}")
            import traceback
            traceback.print_exc()
            return
    
    print("\n" + "=" * 60)
    print("✓ All databases created and tested successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

