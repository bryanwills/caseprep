"""
Database management script for CasePrep.

Usage:
    python scripts/manage_db.py init    # Initialize database with tables
    python scripts/manage_db.py reset   # Reset database (drop and recreate)
    python scripts/manage_db.py sample  # Add sample data
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import our app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.init_db import create_tables, create_sample_data


async def reset_database():
    """Reset the database completely."""
    print("🔄 Resetting database...")
    await create_tables()
    print("✅ Database reset completed!")


async def add_sample_data():
    """Add sample data to the database."""
    print("📝 Adding sample data...")
    await create_sample_data()
    print("✅ Sample data added!")


def print_usage():
    """Print usage instructions."""
    print("""
CasePrep Database Management

Usage:
    python scripts/manage_db.py <command>

Commands:
    init    - Initialize database with tables
    reset   - Reset database (drop and recreate all tables)
    sample  - Add sample data for development
    help    - Show this help message

Examples:
    python scripts/manage_db.py init
    python scripts/manage_db.py reset
    python scripts/manage_db.py sample
""")


async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        if command == "init":
            await create_tables()
        elif command == "reset":
            await reset_database()
        elif command == "sample":
            await add_sample_data()
        elif command == "help":
            print_usage()
        else:
            print(f"❌ Unknown command: {command}")
            print_usage()
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())