"""
Database initialization script for CasePrep.

This script creates the database tables and initial data.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import our app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.base import BaseModel
from app.models import *  # Import all models


async def create_tables():
    """Create all database tables."""
    engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=True,  # Enable SQL logging
        pool_pre_ping=True,
    )
    
    try:
        async with engine.begin() as conn:
            # Drop all tables (be careful with this in production!)
            print("Dropping existing tables...")
            await conn.run_sync(BaseModel.metadata.drop_all)
            
            # Create all tables
            print("Creating tables...")
            await conn.run_sync(BaseModel.metadata.create_all)
            
        print("✅ Database tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise
    finally:
        await engine.dispose()


async def create_sample_data():
    """Create sample data for development."""
    engine = create_async_engine(str(settings.DATABASE_URL))
    
    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            # Check if data already exists
            result = await session.execute("SELECT COUNT(*) FROM tenants")
            count = result.scalar()
            
            if count > 0:
                print("Sample data already exists, skipping...")
                return
            
            from app.models.user import Tenant, User, UserRole, SubscriptionPlan
            from app.models.matter import Matter, MatterStatus, MatterPriority
            
            # Create sample tenant
            tenant = Tenant(
                name="Acme Law Firm",
                slug="acme-law",
                plan=SubscriptionPlan.PROFESSIONAL,
                max_users=25,
                max_storage_gb=100,
                max_transcription_hours=50
            )
            session.add(tenant)
            await session.flush()  # Get the ID
            
            # Create sample user (owner)
            user = User(
                tenant_id=tenant.id,
                email="admin@acmelaw.com",
                hashed_password="$2b$12$example_hashed_password",  # This should be properly hashed
                first_name="John",
                last_name="Doe",
                role=UserRole.OWNER,
                is_active=True,
                is_verified=True
            )
            session.add(user)
            
            # Create sample matter
            matter = Matter(
                tenant_id=tenant.id,
                title="Smith vs. Jones Personal Injury Case",
                description="Motor vehicle accident case with multiple depositions",
                case_number="PI-2024-001",
                client_name="Jane Smith",
                status=MatterStatus.ACTIVE,
                priority=MatterPriority.HIGH,
                practice_area="Personal Injury"
            )
            session.add(matter)
            
            await session.commit()
            print("✅ Sample data created successfully!")
            
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        raise
    finally:
        await engine.dispose()


async def main():
    """Main initialization function."""
    print("🚀 Initializing CasePrep database...")
    
    try:
        await create_tables()
        
        if settings.ENVIRONMENT == "development":
            await create_sample_data()
        
        print("✅ Database initialization completed!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())