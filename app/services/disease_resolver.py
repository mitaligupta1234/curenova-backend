"""
Disease Ontology Resolver Service
Normalizes natural-language disease queries and clinical condition terms into
standard Open Targets Platform ontology identifiers (MONDO, EFO, Orphanet).
"""

import json
import logging
import re
import urllib.request
import urllib.parse
from typing import Optional, Tuple, Dict
from sqlalchemy.orm import Session
from ..models.models import Disease, Drug

logger = logging.getLogger("curenova.disease_resolver")

# Verified curated mappings between common query terms and Open Targets ontology IDs
CURATED_DISEASE_MAPPINGS: Dict[str, Tuple[str, str]] = {
    # Key query pattern (lower): (Canonical Name, Open Targets Ontology ID)
    "pulmonary arterial hypertension": ("Pulmonary Arterial Hypertension", "MONDO_0005149"),
    "pulmonary hypertension": ("Pulmonary Arterial Hypertension", "MONDO_0005149"),
    "hypertension": ("Essential Hypertension", "MONDO_0000839"),
    "pah": ("Pulmonary Arterial Hypertension", "MONDO_0005149"),
    "colorectal cancer": ("Colorectal Cancer", "MONDO_0005575"),
    "colon cancer": ("Colorectal Cancer", "MONDO_0005575"),
    "rectal cancer": ("Colorectal Cancer", "MONDO_0005575"),
    "alzheimer's disease": ("Alzheimer's Disease & Neurodegeneration", "MONDO_0004975"),
    "alzheimers disease": ("Alzheimer's Disease & Neurodegeneration", "MONDO_0004975"),
    "alzheimer's": ("Alzheimer's Disease & Neurodegeneration", "MONDO_0004975"),
    "alzheimer": ("Alzheimer's Disease & Neurodegeneration", "MONDO_0004975"),
    "alzheimer's disease & neurodegeneration": ("Alzheimer's Disease & Neurodegeneration", "MONDO_0004975"),
    "breast cancer": ("Breast Carcinoma", "MONDO_0004989"),
    "breast carcinoma": ("Breast Carcinoma", "MONDO_0004989"),
    "severe covid-19 acute respiratory distress": ("Severe COVID-19 Acute Respiratory Distress", "MONDO_0100096"),
    "covid-19": ("Severe COVID-19 Acute Respiratory Distress", "MONDO_0100096"),
    "covid": ("Severe COVID-19 Acute Respiratory Distress", "MONDO_0100096"),
    "treatment-resistant depression": ("Treatment-Resistant Depression", "MONDO_0000508"),
    "depression": ("Major Depressive Disorder", "MONDO_0000508"),
    "parkinson's disease": ("Parkinson's Disease", "MONDO_0005180"),
    "parkinson": ("Parkinson's Disease", "MONDO_0005180"),
    "glioblastoma multiforme": ("Glioblastoma Multiforme", "MONDO_0018177"),
    "glioblastoma": ("Glioblastoma Multiforme", "MONDO_0018177"),
    "type 2 diabetes": ("Type 2 Diabetes Mellitus", "MONDO_0005148"),
    "diabetic nephropathy": ("Diabetic Nephropathy", "MONDO_0005148"),
    "pancreatic cancer": ("Pancreatic Neoplasm", "MONDO_0021040"),
    "pancreatic neoplasm": ("Pancreatic Neoplasm", "MONDO_0021040"),
    "acute myeloid leukemia": ("Acute Myeloid Leukemia", "MONDO_0018827"),
    "aml": ("Acute Myeloid Leukemia", "MONDO_0018827"),
}

ONTOLOGY_PREFIXES = ("MONDO_", "EFO_", "Orphanet_", "HP_", "OBA_")


class DiseaseResolver:
    """
    Resolves disease queries to Open Targets-compatible ontology IDs.
    Preserves existing database entity records where available.
    """

    @classmethod
    def resolve_disease(
        cls,
        query: str,
        db: Optional[Session] = None
    ) -> Tuple[str, Optional[str], Optional[Disease]]:
        """
        Resolves a user query into (resolved_display_name, ontology_id, db_disease_or_none).

        Returns:
            resolved_name: Human-readable disease name
            ontology_id: Open Targets ontology ID (e.g. 'MONDO_0004989') or None if unresolvable
            db_disease: SQLAlchemy Disease model instance if found in DB, else None
        """
        clean_query = query.strip()
        lower_query = clean_query.lower()

        # 1. Direct ontology identifier pass-through
        for prefix in ONTOLOGY_PREFIXES:
            if clean_query.startswith(prefix):
                db_disease = None
                if db:
                    db_disease = db.query(Disease).filter(
                        (Disease.mesh_id == clean_query) | (Disease.name.ilike(f"%{clean_query}%"))
                    ).first()
                display_name = db_disease.name if db_disease else clean_query
                return display_name, clean_query, db_disease

        # 2. Check curated dictionary for exact or partial match
        if lower_query in CURATED_DISEASE_MAPPINGS:
            name, ont_id = CURATED_DISEASE_MAPPINGS[lower_query]
            db_disease = None
            if db:
                db_disease = db.query(Disease).filter(Disease.name.ilike(f"%{name}%")).first()
            return name, ont_id, db_disease

        for key, (name, ont_id) in CURATED_DISEASE_MAPPINGS.items():
            if len(key) >= 5 and key in lower_query:
                db_disease = None
                if db:
                    db_disease = db.query(Disease).filter(Disease.name.ilike(f"%{name}%")).first()
                return name, ont_id, db_disease

        # 3. Check existing database diseases
        db_disease = None
        if db:
            db_disease = db.query(Disease).filter(Disease.name.ilike(clean_query)).first()
            if not db_disease and len(clean_query) >= 5:
                # Partial match only when clean_query is not a generic token
                db_disease = db.query(Disease).filter(Disease.name.ilike(f"%{clean_query}%")).first()
            if db_disease and (clean_query.lower() == db_disease.name.lower() or (len(clean_query) >= 8 and clean_query.lower() in db_disease.name.lower())):
                # Check if database disease name matches our mapping
                d_name_lower = db_disease.name.lower()
                for key, (name, ont_id) in CURATED_DISEASE_MAPPINGS.items():
                    if key == d_name_lower:
                        return db_disease.name, ont_id, db_disease
                return db_disease.name, db_disease.mesh_id, db_disease

        # 4. Dynamic Open Targets GraphQL lookup (live resolution)
        dynamic_id, dynamic_name = cls._query_opentargets_api(clean_query)
        if dynamic_id:
            logger.info("Dynamically resolved query '%s' to %s (%s)", clean_query, dynamic_id, dynamic_name)
            return dynamic_name or clean_query, dynamic_id, db_disease

        # 5. Resolution failed: return display name with None ontology ID
        # DO NOT invent an ontology ID
        fallback_name = db_disease.name if db_disease else clean_query
        return fallback_name, None, db_disease

    @classmethod
    def resolve_drug(
        cls,
        query: str,
        db: Optional[Session] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[Drug]]:
        """
        Resolves a user query into (resolved_display_name, chembl_id, db_drug_or_none).

        Returns:
            resolved_name: Canonical drug name
            chembl_id: ChEMBL identifier (e.g. 'CHEMBL1908360') or None
            db_drug: SQLAlchemy Drug model instance if found in DB, else None
        """
        clean_query = query.strip()
        lower_query = clean_query.lower()

        # 1. Direct ChEMBL ID pass-through
        if clean_query.upper().startswith("CHEMBL"):
            chembl_id = clean_query.upper()
            db_drug = None
            if db:
                db_drug = db.query(Drug).filter(Drug.chembl_id.ilike(chembl_id)).first()
            display_name = db_drug.name if db_drug else chembl_id
            return display_name, chembl_id, db_drug

        # 2. Check existing database drugs (exact match)
        db_drug = None
        if db:
            db_drug = db.query(Drug).filter(
                (Drug.name.ilike(clean_query)) | (Drug.chembl_id.ilike(clean_query))
            ).first()
            if db_drug:
                return db_drug.name, db_drug.chembl_id, db_drug

        # 3. Check ChEMBL cache file
        from pathlib import Path
        chembl_cache_file = Path(__file__).resolve().parent.parent.parent / "ml" / "data" / "chembl" / "chembl_api_cache.json"
        if chembl_cache_file.exists():
            try:
                with open(chembl_cache_file, "r", encoding="utf-8") as f:
                    c_data = json.load(f)
                for cid, info in c_data.items():
                    d_name = (info.get("drug_name") or "").lower()
                    if d_name and (d_name == lower_query):
                        return info.get("drug_name") or clean_query, cid, None
            except Exception as e:
                logger.debug("ChEMBL cache lookup error for drug '%s': %s", clean_query, e)

        # 4. Check Open Targets drug_molecule parquet via DuckDB
        mol_file = Path(__file__).resolve().parent.parent.parent / "ml" / "data" / "open_targets" / "drug_molecule" / "00000000.parquet"
        if mol_file.exists():
            try:
                import duckdb
                con = duckdb.connect()
                hit = con.execute(
                    f"SELECT id, name FROM read_parquet('{mol_file.as_posix()}') WHERE lower(name) = ? LIMIT 1",
                    [lower_query]
                ).fetchone()
                if hit:
                    return hit[1] or clean_query, hit[0], None
            except Exception as e:
                logger.debug("Open Targets drug_molecule parquet lookup error: %s", e)

        # 5. Dynamic Open Targets GraphQL lookup for drugs
        dynamic_id, dynamic_name = cls._query_opentargets_drug_api(clean_query)
        if dynamic_id:
            logger.info("Dynamically resolved drug query '%s' to %s (%s)", clean_query, dynamic_id, dynamic_name)
            return dynamic_name or clean_query, dynamic_id, None

        return None, None, None

    @classmethod
    def _query_opentargets_api(cls, query_string: str) -> Tuple[Optional[str], Optional[str]]:
        """Queries official Open Targets Platform API to find best disease match."""
        url = "https://api.platform.opentargets.org/api/v4/graphql"
        gql = {
            "query": """
            query SearchDisease($queryString: String!) {
              search(queryString: $queryString, entityNames: ["disease"], page: {index: 0, size: 1}) {
                hits {
                  id
                  name
                  entity
                }
              }
            }
            """,
            "variables": {"queryString": query_string}
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(gql).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "CureNova/2.0 biomedical-research-platform"
                }
            )
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                hits = data.get("data", {}).get("search", {}).get("hits", [])
                if hits:
                    first = hits[0]
                    hit_id = first.get("id")
                    hit_name = first.get("name") or ""
                    q_low = query_string.lower().strip()
                    h_low = hit_name.lower().strip()
                    if q_low == h_low or q_low in h_low or h_low in q_low or q_low == (hit_id or "").lower():
                        return hit_id, hit_name
        except Exception as e:
            logger.debug("Open Targets dynamic disease lookup skipped for '%s': %s", query_string, str(e))

        return None, None

    @classmethod
    def _query_opentargets_drug_api(cls, query_string: str) -> Tuple[Optional[str], Optional[str]]:
        """Queries official Open Targets Platform API to find best drug match."""
        url = "https://api.platform.opentargets.org/api/v4/graphql"
        gql = {
            "query": """
            query SearchDrug($queryString: String!) {
              search(queryString: $queryString, entityNames: ["drug"], page: {index: 0, size: 1}) {
                hits {
                  id
                  name
                  entity
                }
              }
            }
            """,
            "variables": {"queryString": query_string}
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(gql).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "CureNova/2.0 biomedical-research-platform"
                }
            )
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                hits = data.get("data", {}).get("search", {}).get("hits", [])
                if hits:
                    first = hits[0]
                    hit_id = first.get("id")
                    hit_name = first.get("name") or ""
                    q_low = query_string.lower().strip()
                    h_low = hit_name.lower().strip()
                    if q_low == h_low or q_low in h_low or h_low in q_low or q_low == (hit_id or "").lower():
                        return hit_id, hit_name
        except Exception as e:
            logger.debug("Open Targets dynamic drug lookup skipped for '%s': %s", query_string, str(e))

        return None, None
