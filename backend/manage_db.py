#!/usr/bin/env python3
"""
Database management script.
Provides commands for database operations.
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from alembic.config import Config
from alembic import command
import structlog

logger = structlog.get_logger()

def run_migrations():
    """Run database migrations"""
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error("Failed to run migrations", error=str(e))
        raise

def create_migration(message):
    """Create a new migration"""
    try:
        alembic_cfg = Config("alembic.ini")
        command.revision(alembic_cfg, autogenerate=True, message=message)
        logger.info("Migration created successfully", message=message)
    except Exception as e:
        logger.error("Failed to create migration", error=str(e))
        raise

def rollback_migration(revision):
    """Rollback to a specific migration"""
    try:
        alembic_cfg = Config("alembic.ini")
        command.downgrade(alembic_cfg, revision)
        logger.info("Migration rollback completed", revision=revision)
    except Exception as e:
        logger.error("Failed to rollback migration", error=str(e))
        raise

def show_migration_history():
    """Show migration history"""
    try:
        alembic_cfg = Config("alembic.ini")
        command.history(alembic_cfg)
    except Exception as e:
        logger.error("Failed to show migration history", error=str(e))
        raise

def show_current_revision():
    """Show current migration revision"""
    try:
        alembic_cfg = Config("alembic.ini")
        command.current(alembic_cfg)
    except Exception as e:
        logger.error("Failed to show current revision", error=str(e))
        raise

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Database management script")
    parser.add_argument("command", choices=[
        "migrate", "create-migration", "rollback", "history", "current", "init"
    ], help="Command to execute")
    parser.add_argument("--message", "-m", help="Migration message")
    parser.add_argument("--revision", "-r", help="Revision to rollback to")
    
    args = parser.parse_args()
    
    try:
        if args.command == "migrate":
            run_migrations()
            print("✓ Database migrations completed")
            
        elif args.command == "create-migration":
            if not args.message:
                print("ERROR: Migration message is required")
                sys.exit(1)
            create_migration(args.message)
            print(f"✓ Migration created: {args.message}")
            
        elif args.command == "rollback":
            if not args.revision:
                print("ERROR: Revision is required")
                sys.exit(1)
            rollback_migration(args.revision)
            print(f"✓ Rolled back to revision: {args.revision}")
            
        elif args.command == "history":
            show_migration_history()
            
        elif args.command == "current":
            show_current_revision()
            
        elif args.command == "init":
            # Import and run the init script
            from init_db import main as init_main
            asyncio.run(init_main())
            
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 