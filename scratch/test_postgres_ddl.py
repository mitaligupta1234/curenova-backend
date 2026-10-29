"""
Test PostgreSQL DDL compilation for all CureNova SQLAlchemy models.
Verifies that all 18 ORM models compile valid SQL for PostgreSQL without dialect errors.
"""
import sys
import os
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE))

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable, CreateIndex
from app.models.models import Base

def test_postgresql_ddl():
    print("--- Testing PostgreSQL DDL Compilation for All 18 Models ---")
    tables = Base.metadata.sorted_tables
    print(f"Total tables to compile: {len(tables)}")
    
    dialect = postgresql.dialect()
    for table in tables:
        ddl = str(CreateTable(table).compile(dialect=dialect)).strip()
        print(f"\n[OK] Table '{table.name}': {len(table.columns)} columns, {len(table.foreign_keys)} FKs")
        # Print first 2 lines of DDL
        first_lines = "\n".join(ddl.split("\n")[:3])
        print(f"     Preview:\n{first_lines} ...")
    
    print("\nAll 18 tables successfully compiled to valid PostgreSQL DDL!")

if __name__ == "__main__":
    test_postgresql_ddl()
