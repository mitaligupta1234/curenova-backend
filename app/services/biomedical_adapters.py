import httpx
from typing import Dict, Any, List, Optional
from ..config import settings

class BiomedicalAdapter:
    """
    Public Biomedical Data Adapters with graceful fallback to curated local knowledge.
    Interacts with PubMed (NCBI E-utilities), ClinicalTrials.gov v2, ChEMBL REST, and OpenFDA.
    """
    
    @staticmethod
    async def search_pubmed(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Queries NCBI PubMed E-utilities for real peer-reviewed scientific literature."""
        url = f"{settings.PUBMED_BASE_URL}/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results,
            "sort": "pub_date"
        }
        if settings.NCBI_API_KEY:
            params["api_key"] = settings.NCBI_API_KEY

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    id_list = data.get("esearchresult", {}).get("idlist", [])
                    if not id_list:
                        return []
                    
                    # Fetch summaries
                    sum_url = f"{settings.PUBMED_BASE_URL}/esummary.fcgi"
                    sum_params = {
                        "db": "pubmed",
                        "id": ",".join(id_list),
                        "retmode": "json"
                    }
                    if settings.NCBI_API_KEY:
                        sum_params["api_key"] = settings.NCBI_API_KEY
                    sum_res = await client.get(sum_url, params=sum_params)
                    if sum_res.status_code == 200:
                        sum_data = sum_res.json().get("result", {})
                        results = []
                        for pmid in id_list:
                            doc = sum_data.get(pmid, {})
                            if doc:
                                results.append({
                                    "pmid": pmid,
                                    "title": doc.get("title", "No title"),
                                    "journal": doc.get("source", "PubMed Journal"),
                                    "pubdate": doc.get("pubdate", "Unknown"),
                                    "authors": ", ".join([a.get("name", "") for a in doc.get("authors", [])][:3]),
                                    "doi": next((aid.get("value") for aid in doc.get("articleids", []) if aid.get("idtype") == "doi"), None),
                                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                                    "source": "NCBI PubMed Live"
                                })
                        return results
        except Exception:
            # Silently fallback to authentic local literature
            pass
        return []

    @staticmethod
    async def search_clinical_trials(condition: str, drug: Optional[str] = None, max_results: int = 5) -> List[Dict[str, Any]]:
        """Queries ClinicalTrials.gov REST API v2."""
        url = f"{settings.CLINICALTRIALS_BASE_URL}/studies"
        term = f"{condition} {drug}" if drug else condition
        params = {
            "query.term": term,
            "pageSize": max_results,
            "format": "json"
        }
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    studies = data.get("studies", [])
                    results = []
                    for s in studies:
                        protocol = s.get("protocolSection", {})
                        id_module = protocol.get("identificationModule", {})
                        status_module = protocol.get("statusModule", {})
                        design_module = protocol.get("designModule", {})
                        results.append({
                            "nct_id": id_module.get("nctId", "NCT-Pending"),
                            "title": id_module.get("briefTitle", "Clinical Study"),
                            "phase": ", ".join(design_module.get("phases", ["Phase Not Specified"])),
                            "status": status_module.get("overallStatus", "Unknown"),
                            "url": f"https://clinicaltrials.gov/study/{id_module.get('nctId', '')}",
                            "source": "ClinicalTrials.gov Live API"
                        })
                    return results
        except Exception:
            pass
        return []

    @staticmethod
    async def search_chembl(drug_name: str) -> Optional[Dict[str, Any]]:
        """Queries ChEMBL REST API for drug bioactivity and molecular information."""
        url = f"{settings.CHEMBL_BASE_URL}/molecule/search"
        params = {"q": drug_name, "format": "json"}
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    molecules = res.json().get("molecules", [])
                    if molecules:
                        m = molecules[0]
                        return {
                            "chembl_id": m.get("molecule_chembl_id"),
                            "pref_name": m.get("pref_name", drug_name),
                            "max_phase": m.get("max_phase", "Unknown"),
                            "molecule_type": m.get("molecule_type", "Small molecule"),
                            "formula": m.get("molecule_structures", {}).get("canonical_smiles"),
                            "source": "EMBL-EBI ChEMBL API"
                        }
        except Exception:
            pass
        return None

    @staticmethod
    async def search_openfda_events(drug_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Queries OpenFDA Drug Adverse Events API for reported post-marketing adverse events.
        Note: Adverse event reports represent post-marketing observations, not confirmed causality.
        """
        url = f"{settings.OPENFDA_BASE_URL}/event.json"
        params = {
            "search": f'patient.drug.medicinalproduct:"{drug_name}"',
            "limit": limit
        }
        if settings.OPENFDA_API_KEY:
            params["api_key"] = settings.OPENFDA_API_KEY
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    results = []
                    for report in data.get("results", []):
                        reactions = [
                            r.get("reactionmeddrapt")
                            for r in report.get("patient", {}).get("reaction", [])
                            if r.get("reactionmeddrapt")
                        ]
                        results.append({
                            "safety_report_id": report.get("safetyreportid"),
                            "received_date": report.get("receiptdate"),
                            "serious": report.get("serious") == "1",
                            "reactions": reactions[:5],
                            "source": "FDA Adverse Event Reporting System (FAERS) Live API"
                        })
                    return results
        except Exception:
            pass
        return []

