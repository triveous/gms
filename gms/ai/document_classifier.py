"""Document Classification Service for analyzing uploaded files.

This module provides LLM-based document classification using Google Generative AI (Gemini).
It classifies documents against a predefined list of grants and returns structured results.

Usage:
    classifier = DocumentClassifier()
    result = classifier.classify_document(
        filename="document.pdf",
        content="extracted text from document"
    )
"""

import json
import logging
from typing import Any

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

import frappe

logger = logging.getLogger("document_classifier")



def fetch_milestone_metrics_configuration() -> dict[str, str]:
    """Fetch metrics configuration from Grant Project Milestone Type."""
    metrics_config = {
        "YEARLY_PLAN": "[]",
        "QUARTERLY_PROGRESS_REPORT": "[]"
    }
    
    # Mapping from Milestone Type Name to Prompt Key
    type_mapping = {
        "Planning Update": "YEARLY_PLAN",
        "Progress Update": "QUARTERLY_PROGRESS_REPORT"
    }

    for milestone_name, prompt_key in type_mapping.items():
        try:
            if not frappe.db.exists("Grant Project Milestone Type", milestone_name):
                logger.warning(f"Grant Project Milestone Type '{milestone_name}' not found.")
                continue
            
            doc = frappe.get_doc("Grant Project Milestone Type", milestone_name)
            
            metrics = []
            for row in doc.table_avgk:
                metrics.append({
                    "title": row.title,
                    "dataType": row.datatype,
                    "code": row.code,
                    "description": row.description,
                    "formatting_instruction": row.formatting_instruction,
                    "allow_multi_values": bool(row.allow_multi_values),
                    "allow_dynamic_title": bool(row.allow_dynamic_title)
                })
            
            metrics_config[prompt_key] = json.dumps(metrics, indent=2)
            
        except Exception as e:
            logger.error(f"Error loading metrics for {milestone_name}: {e}")

    return metrics_config


class DocumentClassifier:
    """Classifies documents against a predefined grant list using LLM."""

    # Grant list is now dynamically loaded from DB
    GRANTS = []

    def _load_grants_from_db(self):
        """Fetch all grants and their projects from the database (title and name only)."""
        try:
            grants = frappe.get_all(
                "Grant",
                fields=["name", "title"],
            )
            print("GRANT ---> ", grants)
            projects = frappe.get_all(
                "Grant Project",
                fields=["name", "grant", "title"],
            )
            print("GRANT PROJECTS ---> ", projects)
            # Map projects to grants
            grant_map = {}
            for grant in grants:
                grant_map[grant["name"]] = {
                    "title": grant["title"],
                    "name": grant["name"],
                    "projects": [],
                }
            print("grant_map ---> ", grant_map)
            for project in projects:
                grant_id = project["grant"]
                if grant_id in grant_map:
                    grant_map[grant_id]["projects"].append({
                        "title": project["title"],
                        "name": project["name"],
                    })
            print("project ---> ", project)
            # Build grant list for prompt
            grant_list = []
            for grant in grant_map.values():
                entry = f'{grant["title"]} [id: {grant["name"]}]'
                if grant["projects"]:
                    project_entries = ", ".join([
                        f'{p["title"]} [id: {p["name"]}]' for p in grant["projects"]
                    ])
                    entry += f' (Projects: {project_entries})'
                grant_list.append(entry)
                
            print("grant_list ---> ", grant_list)
            return grant_list
        except Exception as e:
            logger.error(f"Error loading grants from DB: {e}")
            return ["NO_GRANTS_FOUND"]
    
    EXTRACTION_PROMPT_TEMPLATE = """
    You are a strict structured data extraction engine.

INPUT:
1. Grant list (with grant_id and associated project_ids).
2. Milestone Type IDs.
3. One document (full text).

Grant List {grant_list}
The document may be:
  - YEARLY PLAN
  - QUARTERLY PROGRESS REPORT

The document contains multiple project sections.
Each project section must generate ONE milestone object.

------------------------------------------------------------
STEP 1 — IDENTIFY GRANT
------------------------------------------------------------

Identify the single parent GRANT using:
- Explicit grant name mention
- Project titles
- PI / Co-PI names
- Partner institutions
- Domain references

Rules:
- One document → One parent grant
- Use only provided grant IDs
- Do not hallucinate

Return:
{{
  "grant_name": "",
  "grant_id": ""
}}

------------------------------------------------------------
STEP 2 — IDENTIFY DOCUMENT TYPE
------------------------------------------------------------

If document contains:
- Status (Did Well / On Track / At Risk)
- Budget Spent
- Overall Progress %
- TRL/MRL/CRL/SIRL
- Impact Created

→ QUARTERLY_PROGRESS_REPORT

If document contains:
- Quarter goals
- Planned deliverables
- Budget allocation per quarter
- No status or performance reporting

→ YEARLY_PLAN

Return:
"document_type": "YEARLY_PLAN | QUARTERLY_PROGRESS_REPORT"

------------------------------------------------------------
STEP 3 — IDENTIFY TIMELINE
------------------------------------------------------------

Extract:

- program_year (e.g., 2025-2026)
- quarter (Q1 | Q2 | Q3 | Q4)
- reporting_period (e.g., "Oct-Dec 2025")

Quarter → Date Mapping:

Q1 (Apr-Jun) → 04-01 to 06-30
Q2 (Jul-Sep) → 07-01 to 09-30
Q3 (Oct-Dec) → 10-01 to 12-31
Q4 (Jan-Mar) → 01-01 to 03-31

Compute:
- period_start
- period_end
- submitted_at = period_endT23:59:59

If reporting period missing → infer from quarter label.

------------------------------------------------------------
STEP 4 — ALLOWED METRICS
------------------------------------------------------------


IF QUARTERLY_PROGRESS_REPORT,
ONLY USE:

{quarterly_progress_metrics}

IF YEARLY_PLAN,
ONLY USE:

{yearly_plan_metrics}

STRICT:
- Do not output metrics outside allowed list.
- Do not invent metric codes.
- Do not duplicate metrics.
- If metric not present → omit.

------------------------------------------------------------
STEP 5 — OUTPUT STRUCTURE AND VALIDATION ERRORS
------------------------------------------------------------

CRITICAL ERROR CHECK:
Before generating the final output, you MUST verify two conditions:
1. PERIOD CHECK: You must check if `period_start` and `period_end` are present in the document or can be inferred. If they are missing, you MUST return an error.
2. PROJECT CHECK: You must check if the projects you found in the document exist in the provided Grant List. If the document references a project that is NOT in the selected Grant ID's project list, you MUST return an error. (It is okay if the document has fewer projects than the Grant List, but NO unknown projects are allowed).

If either condition fails, you MUST stop and return EXACTLY this JSON structure and nothing else:

{{
  "isError": true,
  "errorMessage": "String describing the error (e.g., 'Unknown project found' or 'Reporting period not found in document') very important: message should be small with in 15 words"
}}

If both conditions pass, return the STRICT JSON object below:

{{
  "matched_grant": {{
    "grant_name": "string",
    "grant_id": "string"
  }},
  "document_type": "YEARLY_PLAN | QUARTERLY_PROGRESS_REPORT",
  "timeline": {{
    "program_year": "string",
    "quarter": "Q1 | Q2 | Q3 | Q4",
    "reporting_period": "string",
    "period_start": "YYYY-MM-DD",
    "period_end": "YYYY-MM-DD",
    "submitted_at": "datetime (ISO format)"
  }},
    // You MUST extract ALL project sections in the document.
    // For EACH numbered project section, generate EXACTLY ONE milestone object.
    // The number of milestone objects MUST equal the total number of project sections detected.
    // Do NOT stop after the first project.
    // Do NOT return partial results.
    // If 14 project sections exist, the milestones array MUST contain 14 objects.
    // Each milestone must follow EXACTLY the structure defined below.
  "milestones": [
    {{
      "title": "string",
      "project": "string (Project Name)"
      "projectId": "string (Grant Project ID)",
      "milestone_type": "string (Milestone Type ID)",
      "forecasted_amount": "string (value should be completely numeric like 30000000 instead of 3 cr)",
      "artifacts": [
        {{
          "link": "string",
          "title": "string",
          "description": "string"
        }}
      ],
      "partners": [
        {{
          "partner": "string",
          "responsibility": "string",
          "contributions": "string"
        }}
      ],
      "contributors": [
        {{
          "team_member": "string",
          "role": "string"
        }}
      ],
      "metric_computed_at": "datetime (ISO format)",
      "metrics_values": [
        {{
          "code": "string",
          "title": "string",
          "type": "INT | FLOAT | STRING | BOOLEAN",
          "data_int": integer | null,
          "data_float": float | null,
          "data_string": string | null,
          "data_boolean": boolean | null
        }}
      ]
    }}
  ]
}}


------------------------------------------------------------
FIELD RULES
------------------------------------------------------------

title:
  YEARLY_PLAN → "Q<quarter> <year> Planned Milestone – <Project Name>"
  PROGRESS_REPORT → "Q<quarter> <year> Progress Update – <Project Name>"

forecasted_amount:
  YEARLY_PLAN → Quarter budget allocation
  PROGRESS_REPORT → Budget Spent

metric_computed_at:
  PROGRESS_REPORT → same as submitted_at
  YEARLY_PLAN → null

Metrics data typing:
- INT → fill data_int only
- FLOAT → remove % symbol → fill data_float
- STRING → fill data_string
- BOOLEAN → fill data_boolean
All unused fields must be null.

------------------------------------------------------------
STRICT OUTPUT RULES
------------------------------------------------------------

- Output must be valid JSON
- No markdown
- No comments
- No explanation text
- Use only IDs provided in input
- One milestone per project section
- If value missing → null

------------------------------------------------------------
Document Content:
{document_content}
"""

    VALIDATION_PROMPT_TEMPLATE = """
    You are a data validation engine. You will be provided with extracted milestone data and the source document text.
    Your task is to validate each metric value against the document.

INPUT:
1. Extracted Data (JSON)
2. Source Document (Text)
3. Milestone Period Already Present: {milestone_exists}

Extracted Data:
{extracted_data}

------------------------------------------------------------
VALIDATION RULES
------------------------------------------------------------

For EACH milestone and EACH metric value in the extracted data:
1. isPresent: true if the metric value is found/supported in the document, false otherwise.
2. isCorrectFormat: true if the value matches the expected type (INT, FLOAT, STRING, BOOLEAN) and formatting instructions. false if the type is incorrect or if the value does not follow the format instruection (if the foarmat instruction present then only check the format).
3. If isPresent is false, then isCorrectFormat should be false.
4. errorMessage: if the value is present but the format is wrong, means the metrics value doesn't follow the format instruction then provide the reason, why the value is not following the formatting instruction.

------------------------------------------------------------
OUTPUT STRUCTURE AND VALIDATION ERRORS
------------------------------------------------------------

CRITICAL ERROR CHECK:
Before generating the final output, you MUST verify the following condition:
1. If "Milestone Period Already Present" is true, you MUST return an error because a milestone for this period already exists.

If the condition fails, you MUST stop and return EXACTLY this JSON structure and nothing else:

{{
  "isError": true,
  "errorMessage": "Milestone for this period already exists."
}}

If the condition passes, return the SAME JSON structure as the input, but with "isPresent", "isCorrectFormat", "errorMessage" fields populated for each entry in "metrics_values".

Return STRICT JSON object.

------------------------------------------------------------
Document Content:
{document_content}
"""

    def __init__(self):
        """Initialize the document classifier with LLM and load grants from DB."""
        self.model = None
        self._initialize_model()
        self.GRANTS = self._load_grants_from_db()



    def _initialize_model(self):
        """Initialize the Google Generative AI model."""
        if ChatGoogleGenerativeAI is None:
            logger.warning("ChatGoogleGenerativeAI not available. Install langchain-google-genai.")
            return

        try:
            # Use Gemini 2.0 as per the GMS configuration
            self.model = ChatGoogleGenerativeAI(
                model="gemini-2.5-pro",
                temperature=0.3,  # Lower temperature for more deterministic classification
            )
            logger.info("DocumentClassifier initialized with gemini-2.5-pro")
        except Exception as e:
            logger.error(f"Failed to initialize ChatGoogleGenerativeAI: {e}")
            self.model = None

    def extract_data(
        self,
        filename: str,
        content: str,
        doc_id: str = "doc_1",
    ) -> dict[str, Any]:
        """Extract raw milestone data from the document.

        Args:
            filename: The uploaded filename
            content: The extracted text content from the document
            doc_id: Optional document ID

        Returns:
            Dictionary with extraction results
        """
        if not self.model:
            return {"error": "LLM model not initialized"}

        if not content or len(content.strip()) < 10:
            return {"error": "Document contains insufficient text"}

        try:
            self.GRANTS = self._load_grants_from_db()
            grant_list = "\n".join([f'- "{grant}"' for grant in self.GRANTS])
            metrics_config = fetch_milestone_metrics_configuration()

            prompt = self.EXTRACTION_PROMPT_TEMPLATE.format(
                grant_list=grant_list,
                document_content=content,
                quarterly_progress_metrics=metrics_config.get("QUARTERLY_PROGRESS_REPORT", "[]"),
                yearly_plan_metrics=metrics_config.get("YEARLY_PLAN", "[]")
            )

            response = self.model.invoke(prompt)
            return self._parse_llm_response(response.content.strip())

        except Exception as e:
            return {"error": f"Extraction error: {str(e)}"}

    def update_extraction_task(self, task_id: str, extraction_result: dict[str, Any]) -> None:
        """Update Grant Document Extraction Task with extracted metadata.
        
        Args:
            task_id: The ID of the Grant Document Extraction Task
            extraction_result: The result from extract_data
        """
        if not task_id or extraction_result.get("isError"):
            return

        try:
            timeline = extraction_result.get("timeline", {})
            period_start = timeline.get("period_start")
            period_end = timeline.get("period_end")
            
            matched_grant = extraction_result.get("matched_grant", {})
            grant_id = matched_grant.get("grant_id")
            
            document_type = extraction_result.get("document_type")
            
            updates = {}
            
            if period_start:
                updates["period_start"] = period_start
                updates["isperiodstartpresent"] = 1
                
            if period_end:
                updates["period_end"] = period_end
                updates["isperiodendpresent"] = 1
                
            if grant_id:
                updates["matched_grant"] = grant_id
                
            if document_type == "QUARTERLY_PROGRESS_REPORT":
                updates["milestone_type"] = "Progress Report Extraction"
            elif document_type == "YEARLY_PLAN":
                updates["milestone_type"] = "Yearly Plan Extraction"
                
            if updates:
                frappe.db.set_value("Grant Document Extraction Task", task_id, updates)
                frappe.db.commit()
                logger.info(f"Updated Grant Document Extraction Task {task_id} with {updates}")
                
        except Exception as e:
            logger.error(f"Error updating extraction task {task_id}: {e}")

    def check_milestone_exists(self, extraction_result: dict[str, Any]) -> bool:
        """Check if a milestone for the extracted period already exists in the database."""
        try:
            timeline = extraction_result.get("timeline", {})
            period_start = timeline.get("period_start")
            period_end = timeline.get("period_end")

            if not period_start or not period_end:
                return False

            milestones = extraction_result.get("milestones", [])
            project_ids = []
            for m in milestones:
                if m.get("projectId"):
                    project_ids.append(m.get("projectId"))

            matched_grant = extraction_result.get("matched_grant", {})
            matched_grant_id = matched_grant.get("grant_id")

            if not project_ids and matched_grant_id:
                projects = frappe.get_all("Grant Project", filters={"grant": matched_grant_id}, limit=1, ignore_permissions=True)
                if projects:
                    project_ids = [projects[0].name]

            if project_ids:
                existing = frappe.get_all(
                    "Grant Project Milestone",
                    filters={
                        "project": ["in", project_ids],
                        "milestone_type": "Progress Update",
                        "period_start": period_start,
                        "period_end": period_end,
                        "docstatus": ["<", 2]
                    },
                    limit=1,
                    ignore_permissions=True
                )
                return bool(existing)
        except Exception as e:
            logger.error(f"Error checking existing milestones: {e}")
            
        return False

    def validate_data(
        self,
        extracted_data: dict[str, Any],
        content: str,
        milestone_exists: bool = False
    ) -> dict[str, Any]:
        """Validate extracted milestone data against the source document.

        Args:
            extracted_data: The JSON data to validate
            content: The source text content
            milestone_exists: Whether a milestone for this period already exists

        Returns:
            Validated JSON data
        """
        if not self.model:
            return {"error": "LLM model not initialized"}

        try:
            prompt = self.VALIDATION_PROMPT_TEMPLATE.format(
                extracted_data=json.dumps(extracted_data, indent=2),
                document_content=content,
                milestone_exists="true" if milestone_exists else "false"
            )

            response = self.model.invoke(prompt)
            return self._parse_llm_response(response.content.strip())

        except Exception as e:
            return {"error": f"Validation error: {str(e)}"}

    def classify_document(
        self,
        filename: str,
        content: str,
        doc_id: str = "doc_1",
    ) -> dict[str, Any]:
        """Coordination method for backward compatibility and simplicity."""
        extraction_result = self.extract_data(filename, content, doc_id)
        if "error" in extraction_result:
            return extraction_result

        milestone_exists = self.check_milestone_exists(extraction_result)
        validation_result = self.validate_data(extraction_result, content, milestone_exists)
        return {
            "document_id": doc_id,
            "filename": filename,
            "llm_response": validation_result,
        }

    def _parse_llm_response(self, response_text: str) -> dict[str, Any]:
        """Parse the LLM response to extract JSON.

        Args:
            response_text: The raw response from the LLM

        Returns:
            Parsed JSON as dictionary
        """
        try:
            # Try to parse as JSON directly
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re

            # Look for JSON object in the response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            # If all parsing fails, return a default response
            logger.warning(f"Could not parse LLM response as JSON: {response_text}")
            return {
                "matched_grant": "NO_MATCH",
                "confidence": 0.0,
                "reasoning": "Could not parse LLM response",
            }


def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Extract text content from a file.

    Currently supports PDF files. Other formats can be added as needed.

    Args:
        file_content: Raw file bytes
        filename: Original filename

    Returns:
        Extracted text content
    """
    file_ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if file_ext == "pdf":
        return _extract_text_from_pdf(file_content)
    elif file_ext in ["txt", "text"]:
        return file_content.decode("utf-8", errors="ignore")
    else:
        # For other formats, return a message
        logger.warning(f"Unsupported file format: {file_ext}")
        return f"[Unsupported file format: {file_ext}]"


def _extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file content using pypdf (already in Frappe).

    pypdf is already included as a Frappe dependency, so no additional
    installation is needed.

    Args:
        file_content: Raw PDF bytes

    Returns:
        Extracted text content
    """
    from io import BytesIO

    try:
        from pypdf import PdfReader

        pdf_file = BytesIO(file_content)
        pdf_reader = PdfReader(pdf_file)

        text_content = []
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                text = page.extract_text()
                if text:
                    text_content.append(text)
            except Exception as e:
                logger.warning(f"Failed to extract text from PDF page {page_num}: {e}")

        if text_content:
            logger.info(f"Successfully extracted text from PDF ({len(text_content)} pages)")
            return "\n".join(text_content)
        else:
            logger.warning("No text content extracted from PDF.")
            return "[PDF contains no extractable text]"

    except ImportError:
        logger.error("pypdf library not found. This should not happen as pypdf is a Frappe dependency.")
        return "[PDF extraction unavailable]"
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}", exc_info=True)
        return "[Error extracting PDF content]"
