from __future__ import annotations

import re
from typing import Optional

import numpy as np
import pandas as pd
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer

from jobspy.model import CandidateProfile, Location, Country


class JobMatcher:
    def __init__(self, model_name: str = "Qwen/Qwen3-Embedding-8B"):
        self.model_name = model_name
        self.semantic_model = None
        self._model_loaded = False

    def _load_model(self):
        if not self._model_loaded:
            self.semantic_model = SentenceTransformer(self.model_name)
            self._model_loaded = True

    def _keyword_match_skills(
        self, candidate_skills: list[str], job_text: str
    ) -> float:
        if not candidate_skills or not job_text:
            return 0.0

        job_text_lower = job_text.lower()
        matches = 0
        total_skill_mentions = 0

        for skill in candidate_skills:
            skill_lower = skill.lower()
            count = job_text_lower.count(skill_lower)
            if count > 0:
                matches += 1
                total_skill_mentions += count

        if not candidate_skills:
            return 0.0

        skill_coverage = matches / len(candidate_skills)
        frequency_score = min(total_skill_mentions / (len(job_text) / 100), 1.0)

        return (skill_coverage * 0.7 + frequency_score * 0.3)

    def _keyword_match_title(
        self, candidate_titles: list[str], job_title: str
    ) -> float:
        if not candidate_titles or not job_title:
            return 0.0

        max_similarity = 0.0
        for candidate_title in candidate_titles:
            similarity = fuzz.token_sort_ratio(
                candidate_title.lower(), job_title.lower()
            )
            max_similarity = max(max_similarity, similarity / 100.0)

        return max_similarity

    def _keyword_match_experience(
        self, candidate_years: Optional[float], job_description: str
    ) -> float:
        if candidate_years is None or not job_description:
            return 0.5

        experience_patterns = [
            r"(\d+)\+?\s*years?\s*(?:of\s*)?experience",
            r"(\d+)\+?\s*years?\s*(?:of\s*)?exp",
            r"minimum\s+of\s+(\d+)\s*years?",
            r"at\s+least\s+(\d+)\s*years?",
        ]

        required_years = None
        for pattern in experience_patterns:
            match = re.search(pattern, job_description, re.IGNORECASE)
            if match:
                required_years = float(match.group(1))
                break

        if required_years is None:
            return 0.5
        if candidate_years >= required_years:
            excess = candidate_years - required_years
            if excess <= 2:
                return 1.0
            elif excess <= 5:
                return 0.9
            else:
                return 0.7
        else:
            deficit = required_years - candidate_years
            if deficit <= 1:
                return 0.8
            elif deficit <= 2:
                return 0.6
            else:
                return 0.3

    def _semantic_match(
        self, resume_text: str, job_descriptions: list[str]
    ) -> np.ndarray:
        if not resume_text or not job_descriptions:
            return np.zeros(len(job_descriptions) if job_descriptions else 0)

        self._load_model()

        resume_embedding = self.semantic_model.encode(
            resume_text, convert_to_numpy=True
        )
        job_embeddings = self.semantic_model.encode(
            job_descriptions, convert_to_numpy=True, show_progress_bar=False
        )

        resume_embedding = resume_embedding / np.linalg.norm(resume_embedding)
        job_embeddings = job_embeddings / np.linalg.norm(
            job_embeddings, axis=1, keepdims=True
        )

        similarities = np.dot(job_embeddings, resume_embedding)

        similarities = np.clip(similarities, 0, 1)

        return similarities

    def _parse_location_string(self, location_str: str) -> dict:
        if not location_str:
            return {"city": None, "state": None, "country": None}

        parts = [p.strip() for p in location_str.split(",")]
        result = {"city": None, "state": None, "country": None}

        if len(parts) >= 1:
            result["city"] = parts[0]
        if len(parts) >= 2:
            if len(parts[1]) == 2 and parts[1].isupper():
                result["state"] = parts[1]
            else:
                result["country"] = parts[1]
        if len(parts) >= 3:
            result["country"] = parts[2]

        return result

    def _location_match(
        self,
        candidate_location: Optional[Location],
        preferred_locations: Optional[list[str]],
        job_location: Optional[str],
        is_remote: Optional[bool],
    ) -> float:
        target_locations = []
        if preferred_locations:
            target_locations = [self._parse_location_string(loc) for loc in preferred_locations]
        elif candidate_location:
            target_locations.append({
                "city": candidate_location.city,
                "state": candidate_location.state,
                "country": candidate_location.country.value[0] if isinstance(candidate_location.country, Country) else str(candidate_location.country) if candidate_location.country else None,
            })

        if not target_locations or not job_location:
            if is_remote:
                return 0.7
            return 0.5

        job_loc = self._parse_location_string(job_location)

        if is_remote:
            return 0.7

        max_score = 0.0
        for target_loc in target_locations:
            score = 0.0

            if (
                target_loc["city"]
                and job_loc["city"]
                and target_loc["city"].lower() == job_loc["city"].lower()
                and target_loc["state"]
                and job_loc["state"]
                and target_loc["state"].upper() == job_loc["state"].upper()
            ):
                score = 1.0
            
            elif (
                target_loc["city"]
                and job_loc["city"]
                and target_loc["city"].lower() == job_loc["city"].lower()
            ):
                score = 0.8
            
            elif (
                target_loc["state"]
                and job_loc["state"]
                and target_loc["state"].upper() == job_loc["state"].upper()
            ):
                score = 0.6
            
            elif target_loc["country"] and job_loc["country"]:
                target_country = target_loc["country"].lower()
                job_country = job_loc["country"].lower()
                
                if target_country in job_country or job_country in target_country:
                    score = 0.4
                
                try:
                    target_country_enum = Country.from_string(target_country)
                    job_country_enum = Country.from_string(job_country)
                    if target_country_enum == job_country_enum:
                        score = 0.4
                except ValueError:
                    pass

            max_score = max(max_score, score)

        if max_score == 0.0:
            return 0.2

        return max_score

    def match_jobs(
        self,
        candidate_profile: CandidateProfile,
        jobs_df: pd.DataFrame,
        match_weights: Optional[dict] = None,
    ) -> pd.DataFrame:
        
        if jobs_df.empty:
            return jobs_df

        weights = match_weights or {
            "semantic": 0.4,
            "keyword": 0.3,
            "location": 0.2,
            "experience": 0.1,
        }

        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}

        job_titles = jobs_df["title"].fillna("").astype(str).tolist()
        job_descriptions = (
            (jobs_df["description"].fillna("") + " " + jobs_df["title"].fillna(""))
            .astype(str)
            .tolist()
        )
        job_locations = jobs_df["location"].fillna("").astype(str).tolist()
        is_remote = jobs_df["is_remote"].fillna(False).astype(bool).tolist()

        keyword_scores = []
        for i, (title, desc) in enumerate(zip(job_titles, job_descriptions)):
            skills_score = self._keyword_match_skills(
                candidate_profile.skills, desc
            )
            title_score = self._keyword_match_title(
                candidate_profile.job_titles, title
            )
            experience_score = self._keyword_match_experience(
                candidate_profile.experience_years, desc
            )

            keyword_score = (skills_score * 0.5 + title_score * 0.5)
            keyword_scores.append({
                "keyword": keyword_score,
                "experience": experience_score,
            })

        resume_text = candidate_profile.raw_text or " ".join(
            candidate_profile.skills + candidate_profile.job_titles
        )
        semantic_scores = self._semantic_match(resume_text, job_descriptions)

        location_scores = []
        for job_loc, remote in zip(job_locations, is_remote):
            score = self._location_match(
                candidate_profile.location,
                candidate_profile.preferred_locations,
                job_loc,
                remote,
            )
            location_scores.append(score)

        match_scores = []
        for i in range(len(jobs_df)):
            composite = (
                semantic_scores[i] * weights["semantic"]
                + keyword_scores[i]["keyword"] * weights["keyword"]
                + location_scores[i] * weights["location"]
                + keyword_scores[i]["experience"] * weights["experience"]
            )
            match_scores.append(composite)

        result_df = jobs_df.copy()
        result_df["match_score"] = match_scores

        result_df = result_df.sort_values("match_score", ascending=False).reset_index(
            drop=True
        )

        return result_df

