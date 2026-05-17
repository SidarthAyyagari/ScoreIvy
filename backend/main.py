from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from sqlalchemy import text
from app.routers import questions, tests, users, packages, auth, test_results, sections, admin
from app.db.database import engine, SessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="ScoreIvy API", version="1.0.0")

def check_database_connection():
    """Check database connection health"""
    try:
        logger.info("Checking database connection...")
        db = SessionLocal()
        try:
            # Simple query to test connection
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            logger.info("✅ Database connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {str(e)}")
            raise
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Failed to establish database connection: {str(e)}")
        raise

def run_initialization_script():
    """Run initialization SQL scripts to ensure database is fully set up"""
    try:
        logger.info("Running database initialization scripts...")
        db = SessionLocal()
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Check if tables exist by trying to query users table
            tables_exist = False
            try:
                db.execute(text("SELECT 1 FROM users LIMIT 1"))
                tables_exist = True
                logger.info("✅ Database tables already exist")
            except Exception:
                tables_exist = False
                logger.info("⚠️  Database tables not found, will create schema...")
            
            # If tables don't exist, create them
            if not tables_exist:
                logger.info("Creating database schema...")
                schema_path = os.path.join(base_path, "database", "01_init_database.sql")
                
                if os.path.exists(schema_path):
                    with open(schema_path, 'r') as f:
                        schema_script = f.read()
                    
                    # Execute schema creation statements
                    # Split by semicolon, but preserve multi-line statements
                    # Remove comments first
                    lines = schema_script.split('\n')
                    cleaned_lines = []
                    for line in lines:
                        # Remove inline comments
                        if '--' in line:
                            line = line[:line.index('--')]
                        line = line.strip()
                        if line:
                            cleaned_lines.append(line)
                    
                    # Join and split by semicolon
                    full_script = ' '.join(cleaned_lines)
                    statements = [s.strip() for s in full_script.split(';') if s.strip()]
                    
                    for statement in statements:
                        if statement and not statement.lower().startswith('create database'):
                            try:
                                db.execute(text(statement))
                            except Exception as e:
                                # Ignore "already exists" errors for IF NOT EXISTS statements
                                error_msg = str(e).lower()
                                if "already exists" not in error_msg and "does not exist" not in error_msg:
                                    logger.warning(f"Schema statement warning: {str(e)}")
                    
                    db.commit()
                    logger.info("✅ Database schema created")
                else:
                    logger.warning(f"⚠️  Schema script not found at {schema_path}")
            
            # Run sample data script (always try, uses ON CONFLICT DO NOTHING)
            logger.info("Loading sample data...")
            sample_data_path = os.path.join(base_path, "database", "02_sample_data.sql")
            
            if os.path.exists(sample_data_path):
                with open(sample_data_path, 'r') as f:
                    sample_script = f.read()
                
                # Execute sample data statements
                # Remove comments first
                lines = sample_script.split('\n')
                cleaned_lines = []
                for line in lines:
                    # Remove inline comments
                    if '--' in line:
                        line = line[:line.index('--')]
                    line = line.strip()
                    if line:
                        cleaned_lines.append(line)
                
                # Join and split by semicolon
                full_script = ' '.join(cleaned_lines)
                statements = [s.strip() for s in full_script.split(';') if s.strip()]
                
                for statement in statements:
                    if statement:
                        try:
                            db.execute(text(statement))
                        except Exception as e:
                            # Log but continue - ON CONFLICT DO NOTHING should handle duplicates
                            error_msg = str(e).lower()
                            if "duplicate key" not in error_msg and "already exists" not in error_msg:
                                logger.debug(f"Sample data statement note: {str(e)}")
                
                db.commit()
                logger.info("✅ Sample data loaded")
            else:
                logger.warning(f"⚠️  Sample data script not found at {sample_data_path}")
            
            # Run migration script to ensure schema is up to date
            logger.info("Running database migration script...")
            migration_path = os.path.join(base_path, "database", "06_migrate_test_sections.sql")
            
            if os.path.exists(migration_path):
                with open(migration_path, 'r') as f:
                    migration_script = f.read()
                
                # Execute migration statements
                lines = migration_script.split('\n')
                cleaned_lines = []
                for line in lines:
                    if '--' in line:
                        line = line[:line.index('--')]
                    line = line.strip()
                    if line:
                        cleaned_lines.append(line)
                
                # For migration script, execute the whole script at once for DO $$ blocks
                # PostgreSQL handles DO $$ blocks better when executed as single statement
                try:
                    # Execute the entire migration script as-is
                    db.execute(text(migration_script))
                    db.commit()
                except Exception as e:
                    error_msg = str(e).lower()
                    # If DO $$ block fails, try executing statements one by one
                    if "unexpected end" in error_msg or "syntax error" in error_msg:
                        logger.warning("DO $$ block syntax issue, trying alternative approach...")
                        db.rollback()
                        # Execute statements without DO $$ block
                        statements = [s.strip() for s in full_script.split(';') if s.strip() and 'DO $$' not in s.upper()]
                        for statement in statements:
                            if statement and 'END $$' not in statement.upper():
                                try:
                                    db.execute(text(statement))
                                except Exception as e2:
                                    error_msg2 = str(e2).lower()
                                    if "already exists" not in error_msg2 and "duplicate" not in error_msg2:
                                        logger.debug(f"Migration statement note: {str(e2)}")
                        db.commit()
                    else:
                        # Log but don't fail - migration might already be done
                        if "already exists" not in error_msg and "duplicate" not in error_msg:
                            logger.warning(f"Migration warning: {str(e)}")
                        db.rollback()
                
                db.commit()
                logger.info("✅ Database migration completed")

            admin_migration_path = os.path.join(base_path, "database", "08_add_user_is_admin.sql")
            if os.path.exists(admin_migration_path):
                with open(admin_migration_path, 'r') as f:
                    admin_migration_script = f.read()
                try:
                    db.execute(text(admin_migration_script))
                    db.commit()
                    logger.info("✅ Admin column migration completed")
                except Exception as e:
                    error_msg = str(e).lower()
                    if "already exists" not in error_msg:
                        logger.warning(f"Admin migration warning: {str(e)}")
                    db.rollback()
            
            # Finally, load comprehensive data
            logger.info("Loading comprehensive test data...")
            comprehensive_path = os.path.join(base_path, "database", "05_comprehensive_data.sql")
            
            if os.path.exists(comprehensive_path):
                with open(comprehensive_path, 'r') as f:
                    comprehensive_script = f.read()
                
                # Execute comprehensive data script
                # Remove comments first
                lines = comprehensive_script.split('\n')
                cleaned_lines = []
                for line in lines:
                    # Remove inline comments
                    if '--' in line:
                        line = line[:line.index('--')]
                    line = line.strip()
                    if line:
                        cleaned_lines.append(line)
                
                # Join and split by semicolon
                full_script = ' '.join(cleaned_lines)
                statements = [s.strip() for s in full_script.split(';') if s.strip()]
                
                executed_count = 0
                error_count = 0
                skipped_count = 0
                
                logger.info(f"Parsed {len(statements)} statements from comprehensive data script")
                
                for i, statement in enumerate(statements):
                    if statement:
                        try:
                            db.execute(text(statement))
                            executed_count += 1
                            if executed_count <= 5:  # Log first 5 successful statements
                                logger.debug(f"Executed statement {executed_count}: {statement[:80]}...")
                        except Exception as e:
                            # If transaction is aborted, rollback and continue with next statement
                            error_msg = str(e).lower()
                            if "infailedsqltransaction" in error_msg or "current transaction is aborted" in error_msg:
                                db.rollback()
                                logger.warning(f"Transaction aborted at statement {i+1}, rolling back and continuing...")
                                # Retry the statement after rollback
                                try:
                                    db.execute(text(statement))
                                    executed_count += 1
                                except Exception as e2:
                                    error_msg2 = str(e2).lower()
                                    if "duplicate key" in error_msg2 or "already exists" in error_msg2:
                                        skipped_count += 1
                                    else:
                                        if error_count < 10:
                                            logger.warning(f"Retry failed for statement {i+1}: {str(e2)[:200]}")
                                        error_count += 1
                            elif "duplicate key" in error_msg or "already exists" in error_msg:
                                skipped_count += 1
                            else:
                                if error_count < 10:  # Log first 10 errors
                                    logger.warning(f"Data statement error ({i+1}): {str(e)[:200]}")
                                error_count += 1
                
                db.commit()
                logger.info(f"✅ Comprehensive data loaded ({executed_count} executed, {skipped_count} skipped, {error_count} errors)")
            else:
                logger.warning(f"⚠️  Comprehensive data script not found at {comprehensive_path}")
            
            logger.info("✅ Database initialization completed successfully")
        except Exception as e:
            logger.error(f"❌ Error running initialization script: {str(e)}", exc_info=True)
            db.rollback()
            raise
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Failed to run initialization script: {str(e)}", exc_info=True)
        # Don't fail startup if initialization script fails (but log it)
        logger.warning("⚠️  Continuing startup despite initialization script error...")

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 ScoreIvy API starting up...")
    try:
        # Check database connection (fail if unhealthy)
        check_database_connection()
        
        # Run initialization script
        run_initialization_script()
        
        logger.info("✅ ScoreIvy API startup complete")
    except Exception as e:
        logger.error(f"❌ Fatal error during startup: {str(e)}")
        logger.error("❌ Application startup failed. Exiting...")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("ScoreIvy API shutting down...")

# CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # ui_user
        "http://localhost:3001",  # ui_admin
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(sections.router, prefix="/api/sections", tags=["sections"])
app.include_router(questions.router, prefix="/api/questions", tags=["questions"])
app.include_router(tests.router, prefix="/api/tests", tags=["tests"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(packages.router, prefix="/api/packages", tags=["packages"])
app.include_router(test_results.router, prefix="/api/test-results", tags=["test-results"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/")
async def root():
    return {"message": "ScoreIvy API"}


@app.get("/api/health")
async def health_check():
    from app.routers.auth import is_skip_admin_auth_enabled

    return {
        "status": "healthy",
        "skip_admin_auth": is_skip_admin_auth_enabled(),
    }

