'''
Main: Teiko Technical Assignment
Sub: load_data.py


Author: William McLain
Date: 2026-04-12
Version: 1.0.0
'''

'''
Requirements:
The script must be named `load_data.py` and located in the root directory (not in subdirectories like `src/`).
 - When executed with `python load_data.py`, it should create a SQLite database file (`.db` extension) in the repository root.
- The script should be executable directly without command-line arguments or module-style execution (`python -m`).
'''


#Imports and Libraries
import sqlite3
import csv
import os



#csv file input 
CSV_FILE = "data/cell-count.csv"

#database creation
DB_FILE = "cell_counts.db"


def init_db(conn):
    cursor = conn.cursor()

    cursor.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS projects (
            project_id  TEXT PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS subjects (
            subject_id  TEXT PRIMARY KEY,
            project_id  TEXT NOT NULL,
            condition   TEXT,
            age         INTEGER,
            sex         TEXT,
            treatment   TEXT,
            response    TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (project_id)
        );

        CREATE TABLE IF NOT EXISTS samples (
            sample_id                   TEXT PRIMARY KEY,
            subject_id                  TEXT NOT NULL,
            sample_type                 TEXT,
            time_from_treatment_start   INTEGER,
            FOREIGN KEY (subject_id) REFERENCES subjects (subject_id)
        );

        CREATE TABLE IF NOT EXISTS cell_counts (
            cell_count_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id       TEXT NOT NULL UNIQUE,
            b_cell          INTEGER,
            cd8_t_cell      INTEGER,
            cd4_t_cell      INTEGER,
            nk_cell         INTEGER,
            monocyte        INTEGER,
            FOREIGN KEY (sample_id) REFERENCES samples (sample_id)
        );
    """)

    conn.commit()


def load_data(conn, csv_path):
    cursor = conn.cursor()

    projects = set()
    subjects = {}   # subject_id -> row dict
    samples = []
    cell_counts = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            project_id = row["project"]
            subject_id = row["subject"]
            sample_id  = row["sample"]

            projects.add(project_id)

            if subject_id not in subjects:
                subjects[subject_id] = {
                    "subject_id": subject_id,
                    "project_id": project_id,
                    "condition":  row["condition"],
                    "age":        int(row["age"]) if row["age"] else None,
                    "sex":        row["sex"],
                    "treatment":  row["treatment"] if row["treatment"] else None,
                    "response":   row["response"]  if row["response"]  else None,
                }

            samples.append({
                "sample_id":                 sample_id,
                "subject_id":                subject_id,
                "sample_type":               row["sample_type"],
                "time_from_treatment_start": int(row["time_from_treatment_start"])
                                             if row["time_from_treatment_start"] else None,
            })

            cell_counts.append({
                "sample_id":  sample_id,
                "b_cell":     int(row["b_cell"])     if row["b_cell"]     else None,
                "cd8_t_cell": int(row["cd8_t_cell"]) if row["cd8_t_cell"] else None,
                "cd4_t_cell": int(row["cd4_t_cell"]) if row["cd4_t_cell"] else None,
                "nk_cell":    int(row["nk_cell"])     if row["nk_cell"]   else None,
                "monocyte":   int(row["monocyte"])   if row["monocyte"]   else None,
            })

    cursor.executemany(
        "INSERT OR IGNORE INTO projects (project_id) VALUES (?)",
        [(p,) for p in sorted(projects)],
    )

    cursor.executemany(
        """INSERT OR IGNORE INTO subjects
               (subject_id, project_id, condition, age, sex, treatment, response)
           VALUES (:subject_id, :project_id, :condition, :age, :sex, :treatment, :response)""",
        subjects.values(),
    )

    cursor.executemany(
        """INSERT OR IGNORE INTO samples
               (sample_id, subject_id, sample_type, time_from_treatment_start)
           VALUES (:sample_id, :subject_id, :sample_type, :time_from_treatment_start)""",
        samples,
    )

    cursor.executemany(
        """INSERT OR IGNORE INTO cell_counts
               (sample_id, b_cell, cd8_t_cell, cd4_t_cell, nk_cell, monocyte)
           VALUES (:sample_id, :b_cell, :cd8_t_cell, :cd4_t_cell, :nk_cell, :monocyte)""",
        cell_counts,
    )

    conn.commit()

    print(f"Loaded {len(projects)} project(s)")
    print(f"Loaded {len(subjects)} subject(s)")
    print(f"Loaded {len(samples)} sample(s)")
    print(f"Loaded {len(cell_counts)} cell count record(s)")


#main argument below avoids command line arguments
def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path  = os.path.join(script_dir, DB_FILE)
    csv_path = os.path.join(script_dir, CSV_FILE)

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    conn = sqlite3.connect(db_path)
    try:
        init_db(conn)
        load_data(conn, csv_path)
        print(f"\nDatabase created: {db_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()