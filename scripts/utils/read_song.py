
import sys
from pathlib import Path
sys.path.append('c:/Users/dvize/Desktop/Repos/seratosync')
from seratosync.database import read_database_v2_records

db_path = Path("E:/_Serato_/database V2")
records = read_database_v2_records(db_path)
for record in records:
    print(record)
