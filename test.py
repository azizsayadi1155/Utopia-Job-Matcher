import csv
import sqlite3
from jobspy import scrape_jobs

search_term = input("Enter job title (e.g. 'Python Developer'): ").strip()
location = input("Enter location (e.g. 'USA', 'Tunisia', 'France'): ").strip()

jobs = scrape_jobs(
    site_name=["linkedin", "indeed", "google", "bayt"],
    search_term=search_term,
    location=location,
    results_wanted=20,
    country_indeed=location.lower(),
)

print(f"\n✅ Found {len(jobs)} jobs for '{search_term}' in '{location}'")

columns_to_keep = [
    "id",
    "site",
    "title",
    "company",
    "location",
    "date_posted",
    "job_url",
    "is_remote",
    "min_amount",
    "max_amount",
    "currency",
]

jobs_clean = jobs[columns_to_keep]

db_name = "jobs_data.db"
table_name = "jobs"

conn = sqlite3.connect(db_name)
jobs_clean.to_sql(table_name, conn, if_exists="append", index=False)
conn.close()

print(f"💾 Jobs saved to database: {db_name} (table: {table_name})")

output_file = f"jobs_{search_term.replace(' ', '')}_{location.replace(' ', '')}.csv"
jobs_clean.to_csv(output_file, quoting=csv.QUOTE_NONNUMERIC, index=False)
print(f"📄 CSV also saved as: {output_file}")