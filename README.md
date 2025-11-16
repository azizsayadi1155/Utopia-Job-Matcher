# Utopia Job Matcher

**Utopia Job Matcher** is an intelligent job matching system based on [JobSpy](https://github.com/cullenwatson/JobSpy). It extends JobSpy's job scraping capabilities with an AI-powered job matching system that analyzes your resume and matches it with relevant job opportunities using hybrid keyword + semantic matching.

> **Note**: This project is based on JobSpy by Cullen Watson. The job matcher system was added by azizsayadi1155.

## Features

- Scrapes job postings from **LinkedIn**, **Indeed**, **Glassdoor**, **Google**, **ZipRecruiter**, & other job boards concurrently
- Aggregates the job postings in a dataframe
- Proxies support to bypass blocking
- **Job Matcher System**: Intelligently match jobs to your resume using hybrid keyword + semantic matching with regional relevance

![jobspy](https://github.com/cullenwatson/JobSpy/assets/78247585/ec7ef355-05f6-4fd3-8161-a817e31c5c57)

### Installation

```
pip install -U utopia-job-matcher
```

> **Note**: If you're using the original JobSpy, use `pip install -U python-jobspy` instead.

_Python version >= [3.10](https://www.python.org/downloads/release/python-3100/) required_

### Usage

```python
import csv
from jobspy import scrape_jobs

jobs = scrape_jobs(
    site_name=["indeed", "linkedin", "zip_recruiter", "google"], # "glassdoor", "bayt", "naukri", "bdjobs"
    search_term="software engineer",
    google_search_term="software engineer jobs near San Francisco, CA since yesterday",
    location="San Francisco, CA",
    results_wanted=20,
    hours_old=72,
    country_indeed='USA',
    
    # linkedin_fetch_description=True # gets more info such as description, direct job url (slower)
    # proxies=["208.195.175.46:65095", "208.195.175.45:65095", "localhost"],
)
print(f"Found {len(jobs)} jobs")
print(jobs.head())
jobs.to_csv("jobs.csv", quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False) # to_excel
```

### Output

```
SITE           TITLE                             COMPANY           CITY          STATE  JOB_TYPE  INTERVAL  MIN_AMOUNT  MAX_AMOUNT  JOB_URL                                            DESCRIPTION
indeed         Software Engineer                 AMERICAN SYSTEMS  Arlington     VA     None      yearly    200000      150000      https://www.indeed.com/viewjob?jk=5e409e577046...  THIS POSITION COMES WITH A 10K SIGNING BONUS!...
indeed         Senior Software Engineer          TherapyNotes.com  Philadelphia  PA     fulltime  yearly    135000      110000      https://www.indeed.com/viewjob?jk=da39574a40cb...  About Us TherapyNotes is the national leader i...
linkedin       Software Engineer - Early Career  Lockheed Martin   Sunnyvale     CA     fulltime  yearly    None        None        https://www.linkedin.com/jobs/view/3693012711      Description:By bringing together people that u...
linkedin       Full-Stack Software Engineer      Rain              New York      NY     fulltime  yearly    None        None        https://www.linkedin.com/jobs/view/3696158877      Rain’s mission is to create the fastest and ea...
zip_recruiter Software Engineer - New Grad       ZipRecruiter      Santa Monica  CA     fulltime  yearly    130000      150000      https://www.ziprecruiter.com/jobs/ziprecruiter...  We offer a hybrid work environment. Most US-ba...
zip_recruiter Software Developer                 TEKsystems        Phoenix       AZ     fulltime  hourly    65          75          https://www.ziprecruiter.com/jobs/teksystems-0...  Top Skills' Details• 6 years of Java developme...

```

### Parameters for `scrape_jobs()`

```plaintext
Optional
├── site_name (list|str): 
|    linkedin, zip_recruiter, indeed, glassdoor, google, bayt, bdjobs
|    (default is all)
│
├── search_term (str)
|
├── google_search_term (str)
|     search term for google jobs. This is the only param for filtering google jobs.
│
├── location (str)
│
├── distance (int): 
|    in miles, default 50
│
├── job_type (str): 
|    fulltime, parttime, internship, contract
│
├── proxies (list): 
|    in format ['user:pass@host:port', 'localhost']
|    each job board scraper will round robin through the proxies
|
├── is_remote (bool)
│
├── results_wanted (int): 
|    number of job results to retrieve for each site specified in 'site_name'
│
├── easy_apply (bool): 
|    filters for jobs that are hosted on the job board site (LinkedIn easy apply filter no longer works)
|
├── user_agent (str): 
|    override the default user agent which may be outdated
│
├── description_format (str): 
|    markdown, html (Format type of the job descriptions. Default is markdown.)
│
├── offset (int): 
|    starts the search from an offset (e.g. 25 will start the search from the 25th result)
│
├── hours_old (int): 
|    filters jobs by the number of hours since the job was posted 
|    (ZipRecruiter and Glassdoor round up to next day.)
│
├── verbose (int) {0, 1, 2}: 
|    Controls the verbosity of the runtime printouts 
|    (0 prints only errors, 1 is errors+warnings, 2 is all logs. Default is 2.)

├── linkedin_fetch_description (bool): 
|    fetches full description and direct job url for LinkedIn (Increases requests by O(n))
│
├── linkedin_company_ids (list[int]): 
|    searches for linkedin jobs with specific company ids
|
├── country_indeed (str): 
|    filters the country on Indeed & Glassdoor (see below for correct spelling)
|
├── enforce_annual_salary (bool): 
|    converts wages to annual salary
|
├── ca_cert (str)
|    path to CA Certificate file for proxies
```

```
├── Indeed limitations:
|    Only one from this list can be used in a search:
|    - hours_old
|    - job_type & is_remote
|    - easy_apply
│
└── LinkedIn limitations:
|    Only one from this list can be used in a search:
|    - hours_old
|    - easy_apply
```

## Job Matcher System

Utopia Job Matcher includes an intelligent job matching system that analyzes your resume and matches it with relevant job opportunities. The system uses a hybrid approach combining keyword matching and semantic similarity to find the best matches.

### Features

- **Resume Parsing**: Extracts skills, experience, job titles, location, and education from PDF/DOCX resumes
- **Hybrid Matching**: Combines keyword-based matching (skills, titles) with semantic similarity using AI embeddings
- **Regional Relevance**: Prioritizes jobs based on location proximity (exact match > same city > same state > same country)
- **Experience Matching**: Compares your years of experience with job requirements
- **Auto-Scraping**: Automatically scrapes jobs based on your resume profile

### Usage

#### Option 1: Match against existing scraped jobs

```python
from jobspy import scrape_jobs, match_jobs_from_resume

# First, scrape some jobs
jobs = scrape_jobs(
    search_term="software engineer",
    location="San Francisco, CA",
    results_wanted=50
)

# Match jobs to your resume
matched_jobs = match_jobs_from_resume(
    resume_path="resume.pdf",
    jobs_df=jobs
)

# View top matches
print(matched_jobs[['title', 'company', 'location', 'match_score']].head(10))
```

#### Option 2: Auto-scrape and match

```python
from jobspy import match_jobs_from_resume

# Automatically scrape and match jobs based on your resume
matched_jobs = match_jobs_from_resume(
    resume_path="resume.pdf",
    preferred_locations=["San Francisco, CA", "Remote"],
    scrape_params={
        "results_wanted": 50,
        "site_name": ["indeed", "linkedin", "zip_recruiter"]
    }
)

# Results are sorted by match score (highest first)
print(f"Found {len(matched_jobs)} matched jobs")
print(matched_jobs[['title', 'company', 'match_score']].head())
```

#### Option 3: Override location preferences

```python
from jobspy import match_jobs_from_resume, scrape_jobs

jobs = scrape_jobs(search_term="data scientist", location="USA", results_wanted=100)

# Override resume location with preferred locations
matched_jobs = match_jobs_from_resume(
    resume_path="resume.pdf",
    jobs_df=jobs,
    preferred_locations=["New York, NY", "Boston, MA", "Remote"]
)
```

### Parameters for `match_jobs_from_resume()`

```plaintext
Required
├── resume_path (str): 
│    Path to your resume file (PDF or DOCX)

Optional
├── jobs_df (pd.DataFrame): 
│    Pre-scraped jobs DataFrame. If not provided, jobs will be auto-scraped
│    based on your resume profile
│
├── preferred_locations (list[str]): 
│    Override resume location with preferred locations
│    Example: ["San Francisco, CA", "Remote", "New York, NY"]
│
├── scrape_params (dict): 
│    Parameters for auto-scraping if jobs_df is not provided
│    Uses extracted skills/job titles for search_term and location from resume
│    Example: {"results_wanted": 50, "site_name": ["indeed", "linkedin"]}
│
└── match_weights (dict): 
     Customize scoring weights (default shown below)
     {
         "semantic": 0.4,    # Semantic similarity score
         "keyword": 0.3,     # Keyword matching (skills + titles)
         "location": 0.2,    # Regional relevance
         "experience": 0.1   # Experience level match
     }
```

### Matching Algorithm

The job matcher uses a hybrid approach with the following components:

1. **Semantic Matching (40%)**: Uses Qwen/Qwen3-Embedding-8B model to generate embeddings for your resume and job descriptions, then calculates cosine similarity. This captures meaning and context beyond exact keyword matches.

2. **Keyword Matching (30%)**: 
   - **Skills Overlap**: Matches your skills with skills mentioned in job descriptions
   - **Title Similarity**: Uses fuzzy matching to compare your job titles with posting titles

3. **Location Matching (20%)**: Scores jobs based on location proximity:
   - Exact city/state match: 1.0
   - Same city, different state: 0.8
   - Same state: 0.6
   - Same country: 0.4
   - Remote jobs: 0.7 (if applicable)
   - Different country: 0.2

4. **Experience Matching (10%)**: Compares your years of experience with job requirements extracted from descriptions.

The final `match_score` is a weighted combination of all factors, normalized to 0-1 scale. Results are sorted by match score (highest first).

### Supported Resume Formats

- **PDF**: Extracts text using pdfplumber
- **DOCX**: Extracts text using python-docx

### What Gets Extracted from Your Resume

- **Skills**: Technical and soft skills (from skills section and throughout resume)
- **Job Titles**: Historical job titles from work experience
- **Location**: City, state, and country (from contact/header section)
- **Education**: Degrees and institutions
- **Experience**: Total years of experience calculated from work history dates

### Example Output

```python
matched_jobs = match_jobs_from_resume("resume.pdf", jobs_df=jobs)
print(matched_jobs[['title', 'company', 'location', 'match_score']].head())
```

```
                    title              company          location  match_score
0   Senior Software Engineer         Tech Corp    San Francisco, CA        0.92
1   Software Engineer II            StartupXYZ    San Francisco, CA        0.89
2   Full-Stack Developer            BigTech Inc   Remote                  0.87
3   Backend Engineer                CloudCo       San Jose, CA             0.85
4   Software Developer              LocalDev      Oakland, CA              0.83
```

## Supported Countries for Job Searching

### **LinkedIn**

LinkedIn searches globally & uses only the `location` parameter. 

### **ZipRecruiter**

ZipRecruiter searches for jobs in **US/Canada** & uses only the `location` parameter.

### **Indeed / Glassdoor**

Indeed & Glassdoor supports most countries, but the `country_indeed` parameter is required. Additionally, use the `location`
parameter to narrow down the location, e.g. city & state if necessary. 

You can specify the following countries when searching on Indeed (use the exact name, * indicates support for Glassdoor):

|                      |              |            |                |
|----------------------|--------------|------------|----------------|
| Argentina            | Australia*   | Austria*   | Bahrain        |
| Belgium*             | Brazil*      | Canada*    | Chile          |
| China                | Colombia     | Costa Rica | Czech Republic |
| Denmark              | Ecuador      | Egypt      | Finland        |
| France*              | Germany*     | Greece     | Hong Kong*     |
| Hungary              | India*       | Indonesia  | Ireland*       |
| Tunisia              | Italy*       | Japan      | Kuwait         |
| Luxembourg           | Malaysia     | Mexico*    | Morocco        |
| Netherlands*         | New Zealand* | Nigeria    | Norway         |
| Oman                 | Pakistan     | Panama     | Peru           |
| Philippines          | Poland       | Portugal   | Qatar          |
| Romania              | Saudi Arabia | Singapore* | South Africa   |
| South Korea          | Spain*       | Sweden     | Switzerland*   |
| Taiwan               | Thailand     | Turkey     | Ukraine        |
| United Arab Emirates | UK*          | USA*       | Uruguay        |
| Venezuela            | Vietnam*     |            |                |

### **Bayt**

Bayt only uses the search_term parameter currently and searches internationally



## Notes
* Indeed is the best scraper currently with no rate limiting.  
* All the job board endpoints are capped at around 1000 jobs on a given search.  
* LinkedIn is the most restrictive and usually rate limits around the 10th page with one ip. Proxies are a must basically.

## Frequently Asked Questions

---
**Q: Why is Indeed giving unrelated roles?**  
**A:** Indeed searches the description too.

- use - to remove words
- "" for exact match

Example of a good Indeed query

```py
search_term='"engineering intern" software summer (java OR python OR c++) 2025 -tax -marketing'
```

This searches the description/title and must include software, summer, 2025, one of the languages, engineering intern exactly, no tax, no marketing.

---

**Q: No results when using "google"?**  
**A:** You have to use super specific syntax. Search for google jobs on your browser and then whatever pops up in the google jobs search box after applying some filters is what you need to copy & paste into the google_search_term. 

---

**Q: Received a response code 429?**  
**A:** This indicates that you have been blocked by the job board site for sending too many requests. All of the job board sites are aggressive with blocking. We recommend:

- Wait some time between scrapes (site-dependent).
- Try using the proxies param to change your IP address.

---

### JobPost Schema

```plaintext
JobPost
├── title
├── company
├── company_url
├── job_url
├── location
│   ├── country
│   ├── city
│   ├── state
├── is_remote
├── description
├── job_type: fulltime, parttime, internship, contract
├── job_function
│   ├── interval: yearly, monthly, weekly, daily, hourly
│   ├── min_amount
│   ├── max_amount
│   ├── currency
│   └── salary_source: direct_data, description (parsed from posting)
├── date_posted
└── emails

Linkedin specific
└── job_level

Linkedin & Indeed specific
└── company_industry

Indeed specific
├── company_country
├── company_addresses
├── company_employees_label
├── company_revenue_label
├── company_description
└── company_logo

Naukri specific
├── skills
├── experience_range
├── company_rating
├── company_reviews_count
├── vacancy_count
└── work_from_home_type
```

## Credits & Acknowledgments

**Utopia Job Matcher** is based on [JobSpy](https://github.com/cullenwatson/JobSpy) by Cullen Watson and Zachary Hampton.

### Original JobSpy Contributors
- **Cullen Watson** - Original creator and maintainer of JobSpy
- **Zachary Hampton** - Contributor to JobSpy

### Utopia Job Matcher Contributors
- **azizsayadi1155** - Added the intelligent job matching system with resume parsing, hybrid matching, and regional relevance features

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
