from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import pdfplumber
from docx import Document

from jobspy.model import CandidateProfile, Location, Country


def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise ValueError(f"Error reading PDF file: {e}")
    return text


def extract_text_from_docx(file_path: str) -> str:
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        raise ValueError(f"Error reading DOCX file: {e}")


def extract_text_from_resume(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    extension = path.suffix.lower()
    if extension == ".pdf":
        return extract_text_from_pdf(file_path)
    elif extension in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {extension}. Supported formats: .pdf, .docx")


def extract_skills(text: str) -> list[str]:
    technical_skills = [
        r"\b(python|java|javascript|typescript|react|angular|vue|node\.?js|express)\b",
        r"\b(c\+\+|c#|\.net|asp\.net|php|ruby|go|rust|swift|kotlin|scala)\b",
        r"\b(sql|mysql|postgresql|mongodb|redis|elasticsearch|dynamodb)\b",
        r"\b(aws|azure|gcp|docker|kubernetes|terraform|jenkins|ci/cd)\b",
        r"\b(html|css|sass|less|bootstrap|tailwind|jquery)\b",
        r"\b(machine learning|ml|deep learning|ai|tensorflow|pytorch|keras)\b",
        r"\b(git|github|gitlab|bitbucket|svn|mercurial)\b",
        r"\b(linux|unix|bash|shell|powershell)\b",
        r"\b(rest|graphql|api|microservices|soa)\b",
        r"\b(agile|scrum|kanban|jira|confluence)\b",
    ]

    soft_skills = [
        r"\b(leadership|teamwork|communication|problem solving|analytical)\b",
        r"\b(collaboration|project management|time management|organization)\b",
        r"\b(creativity|adaptability|critical thinking|attention to detail)\b",
    ]

    skills = set()
    text_lower = text.lower()

    for pattern in technical_skills:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                skills.add(match[0].lower())
            else:
                skills.add(match.lower())

    for pattern in soft_skills:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                skills.add(match[0].lower())
            else:
                skills.add(match.lower())

    skills_section_patterns = [
        r"skills?[:\s]+(.*?)(?:\n\n|\n[A-Z]|$)",
        r"technical skills?[:\s]+(.*?)(?:\n\n|\n[A-Z]|$)",
        r"core competencies?[:\s]+(.*?)(?:\n\n|\n[A-Z]|$)",
        r"technologies?[:\s]+(.*?)(?:\n\n|\n[A-Z]|$)",
    ]

    for pattern in skills_section_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            skills_text = match.group(1)
            skill_items = re.split(r"[,;•\-\n\|]", skills_text)
            for item in skill_items:
                item = item.strip()
                if item and len(item) > 2 and len(item) < 50:
                    skills.add(item.lower())

    return sorted(list(skills))


def extract_job_titles(text: str) -> list[str]:
    titles = []
    
    title_patterns = [
        r"(?:^|\n)\s*(?:Senior|Junior|Lead|Principal|Staff|Associate)?\s*"
        r"(Software|Data|DevOps|ML|AI|Backend|Frontend|Full.?Stack|Mobile|QA|Test|Security)?\s*"
        r"(Engineer|Developer|Programmer|Architect|Scientist|Analyst|Manager|Director|Specialist|Consultant)",
        r"(?:^|\n)\s*(Product|Project|Engineering|Technical|Software|Data|IT)?\s*"
        r"(Manager|Lead|Director|Head|VP|Vice President)",
    ]

    experience_patterns = [
        r"experience[:\s]+(.*?)(?:\n\n\n|\n[A-Z]{3,}|education|$)",
        r"work history[:\s]+(.*?)(?:\n\n\n|\n[A-Z]{3,}|education|$)",
        r"employment[:\s]+(.*?)(?:\n\n\n|\n[A-Z]{3,}|education|$)",
    ]

    experience_text = ""
    for pattern in experience_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            experience_text = match.group(1)
            break

    if not experience_text:
        experience_text = text

    for pattern in title_patterns:
        matches = re.findall(pattern, experience_text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            if isinstance(match, tuple):
                title = " ".join([m for m in match if m]).strip()
            else:
                title = match.strip()
            if title and len(title) > 3 and len(title) < 100:
                titles.append(title)

    lines = text.split("\n")
    for i, line in enumerate(lines):
        line = line.strip()
        if any(keyword in line.lower() for keyword in ["engineer", "developer", "manager", "analyst", "scientist", "architect"]):
            if i + 1 < len(lines) and lines[i + 1].strip():
                titles.append(line)

    return list(set(titles))[:10]


def extract_location(text: str) -> Optional[Location]:
    location_patterns = [
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*([A-Z]{2})\s*(?:,\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?))?",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+([A-Z]{2})",
    ]

    header_patterns = [
        r"(?:location|address|city)[:\s]+(.*?)(?:\n|$)",
        r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:,\s*[A-Z]{2})?(?:,\s*[A-Z][a-z]+)?)",
    ]

    location_text = ""
    for pattern in header_patterns:
        match = re.search(pattern, text[:500], re.IGNORECASE | re.MULTILINE)
        if match:
            location_text = match.group(1) if match.groups() else match.group(0)
            break

    if not location_text:
        lines = text.split("\n")[:10]
        for line in lines:
            for pattern in location_patterns:
                match = re.search(pattern, line)
                if match:
                    location_text = line
                    break
            if location_text:
                break

    if location_text:
        parts = re.split(r",\s*", location_text.strip())
        city = None
        state = None
        country = None

        if len(parts) >= 1:
            city = parts[0].strip()
        if len(parts) >= 2:
            state_or_country = parts[1].strip()
            if len(state_or_country) == 2 and state_or_country.isupper():
                state = state_or_country
            else:
                country = state_or_country
        if len(parts) >= 3:
            country = parts[2].strip()

        country_enum = None
        if country:
            try:
                country_enum = Country.from_string(country)
            except ValueError:
                pass

        return Location(city=city, state=state, country=country_enum or country)

    return None


def extract_education(text: str) -> list[str]:
    education = []

    education_patterns = [
        r"education[:\s]+(.*?)(?:\n\n\n|\n[A-Z]{3,}|experience|work|skills|$)",
        r"academic[:\s]+(.*?)(?:\n\n\n|\n[A-Z]{3,}|experience|work|skills|$)",
    ]

    education_text = ""
    for pattern in education_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            education_text = match.group(1)
            break

    if education_text:
        degree_patterns = [
            r"\b(B\.?S\.?|B\.?A\.?|B\.?E\.?|M\.?S\.?|M\.?A\.?|M\.?E\.?|M\.?B\.?A\.?|Ph\.?D\.?|Doctorate)\b",
            r"\b(Bachelor|Master|Doctor|PhD|Associate|Engineer|Licence|Mastère|Ingenieur|Cycle)\s+(of|in)\s+[A-Z][a-z]+",
        ]

        for pattern in degree_patterns:
            matches = re.findall(pattern, education_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    degree = " ".join([m for m in match if m]).strip()
                else:
                    degree = match.strip()
                if degree:
                    education.append(degree)

    return list(set(education))


def calculate_experience_years(text: str) -> Optional[float]:
    date_patterns = [
        r"(\d{4}|\w+\s+\d{4})\s*[-–—]\s*(\d{4}|\w+\s+\d{4}|present|current)",
        r"(\w+\s+\d{4})\s*[-–—]\s*(\w+\s+\d{4}|present|current)",
    ]

    experience_text = ""
    experience_section_patterns = [
        r"experience[:\s]+(.*?)(?:\n\n\n|\n[A-Z]{3,}|education|$)",
        r"work history[:\s]+(.*?)(?:\n\n\n|\n[A-Z]{3,}|education|$)",
    ]

    for pattern in experience_section_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            experience_text = match.group(1)
            break

    if not experience_text:
        experience_text = text

    total_months = 0
    current_year = datetime.now().year
    current_month = datetime.now().month

    for pattern in date_patterns:
        matches = re.findall(pattern, experience_text, re.IGNORECASE)
        for match in matches:
            start_str, end_str = match

            try:
                if len(start_str) == 4 and start_str.isdigit():
                    start_year = int(start_str)
                    start_month = 1
                else:
                    parts = start_str.split()
                    if len(parts) == 2:
                        month_name = parts[0]
                        year = int(parts[1])
                        month_map = {
                            "january": 1, "february": 2, "march": 3, "april": 4,
                            "may": 5, "june": 6, "july": 7, "august": 8,
                            "september": 9, "october": 10, "november": 11, "december": 12,
                            "jan": 1, "feb": 2, "mar": 3, "apr": 4,
                            "may": 5, "jun": 6, "jul": 7, "aug": 8,
                            "sep": 9, "oct": 10, "nov": 11, "dec": 12,
                        }
                        start_month = month_map.get(month_name.lower(), 1)
                        start_year = year
                    else:
                        continue
            except (ValueError, IndexError):
                continue

            try:
                if end_str.lower() in ["present", "current"]:
                    end_year = current_year
                    end_month = current_month
                elif len(end_str) == 4 and end_str.isdigit():
                    end_year = int(end_str)
                    end_month = 12
                else:
                    parts = end_str.split()
                    if len(parts) == 2:
                        month_name = parts[0]
                        year = int(parts[1])
                        month_map = {
                            "january": 1, "february": 2, "march": 3, "april": 4,
                            "may": 5, "june": 6, "july": 7, "august": 8,
                            "september": 9, "october": 10, "november": 11, "december": 12,
                            "jan": 1, "feb": 2, "mar": 3, "apr": 4,
                            "may": 5, "jun": 6, "jul": 7, "aug": 8,
                            "sep": 9, "oct": 10, "nov": 11, "dec": 12,
                        }
                        end_month = month_map.get(month_name.lower(), 12)
                        end_year = year
                    else:
                        continue
            except (ValueError, IndexError):
                continue

            start_total = start_year * 12 + start_month
            end_total = end_year * 12 + end_month
            total_months += max(0, end_total - start_total)

    if total_months > 0:
        return round(total_months / 12.0, 1)

    return None


def parse_resume(file_path: str) -> CandidateProfile:
    raw_text = extract_text_from_resume(file_path)
    skills = extract_skills(raw_text)
    job_titles = extract_job_titles(raw_text)
    location = extract_location(raw_text)
    education = extract_education(raw_text)
    experience_years = calculate_experience_years(raw_text)

    return CandidateProfile(
        skills=skills,
        experience_years=experience_years,
        job_titles=job_titles,
        location=location,
        education=education,
        raw_text=raw_text,
    )

