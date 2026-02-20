import frappe
import json
from gms.ai.document_classifier import DocumentClassifier, extract_text_from_file


@frappe.whitelist(allow_guest=True)
def resume_with_file():
    """Resume an interrupted thread with uploaded file data and classification.
    
    This endpoint:
    1. Validates the thread_id and file upload
    2. Extracts text content from the uploaded file (uses pypdf, already in Frappe)
    3. Classifies the document using LLM
    4. Logs the results to console
    5. Saves classification for the agent to present to user
    6. Resumes agent execution with the file data
    
    Expected form data:
        - thread_id: The thread ID that was interrupted
        - file: The uploaded file
        - request_id: Optional request ID from the interrupt
    
    Returns:
        SSE stream with agent response
    """
    # Validate thread_id
    thread_id = frappe.form_dict.get("thread_id")
    if not thread_id:
        frappe.response["http_status_code"] = 400
        frappe.throw("Missing thread_id")
        return

    request_id = frappe.form_dict.get("request_id")

    # Validate file upload
    file = frappe.request.files.get("file")
    if not file:
        frappe.response["http_status_code"] = 400
        frappe.throw("Missing file")
        return

    try:
        # Read file data
        import base64
        import uuid
        
        file_content = file.read()
        
        # Extract text from file based on format
        extracted_text = extract_text_from_file(file_content, file.filename)
        
        # Classify the document using LLM
        classifier = DocumentClassifier()
        classification_result = classifier.classify_document(
            filename=file.filename,
            content=extracted_text,
            doc_id="uploaded_document"
        )
        
        # Log the classification result to console
        print("\n" + "="*80)
        print("DOCUMENT CLASSIFICATION RESULT")
        print("="*80)
        print(f"RESULT ---------> : {classification_result}")
        grant_name = classification_result.get('matched_grant')
        grant_id = classification_result.get('matched_grant_id')
        # print(f"Matched Grant: {grant_name} (ID: {grant_id})")
        confidence = classification_result.get('confidence')
        try:
            confidence_val = float(confidence)
        except (TypeError, ValueError):
            confidence_val = 0.0
        print(f"Confidence Score: {confidence_val:.2%}")
        print(f"Reasoning: {classification_result.get('reasoning')}")
        if 'error' in classification_result:
            print(f"Error: {classification_result['error']}")
        print("="*80)
        print("⏳ Waiting for user confirmation...\n")
        
        # Save the uploaded file to Frappe's File doctype
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file.filename,
            "is_private": 1,
            "content": file_content
        })
        file_doc.save(ignore_permissions=True)
        file_id = file_doc.name
        print(f"File saved with ID: {file_id}")
        
        # Save classification to thread for the agent to access
        try:
            frappe.db.set_value(
                "AI Thread",
                thread_id,
                "_last_file_classification",
                json.dumps(classification_result),
                update_modified=False
            )
        except Exception:
            # Silently fail - classification saving is not critical
            pass
        
        response_data = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_content),
            "extracted_text": extracted_text[:2000],
            "classification": classification_result,
            "request_id": request_id,
            "file_id": file_id,
        }
        frappe.response["http_status_code"] = 200
        frappe.response["Content-Type"] = "application/json"
        frappe.response["data"] = response_data
        return response_data

    except Exception as e:
        frappe.response["http_status_code"] = 500
        error_msg = f"Error processing file: {str(e)}"
        print(f"\nERROR in resume_with_file: {error_msg}\n")
        frappe.throw(error_msg)


@frappe.whitelist(allow_guest=True)
def submit_extracted_milestone():
    """API to accept submit/reject for extracted milestone data.
    Expects:
        - submit: true/false (boolean or string)
        - extracted_data: The classification result data (JSON string or dict)
        - file_id: ID of the uploaded file to attach to milestones
    """
    try:
        submit = frappe.form_dict.get("submit")
        extracted_data_param = frappe.form_dict.get("extracted_data")
        file_id = frappe.form_dict.get("file_id")
        
        if submit is None or extracted_data_param is None:
            frappe.response["http_status_code"] = 400
            frappe.throw("Missing required parameters: submit, extracted_data")
            return
        
        # file_id is optional - only needed when submit is True
        if submit and not file_id:
            print("Warning: No file_id provided for milestone creation")
        
        # Parse boolean
        if isinstance(submit, str):
            submit = submit.lower() == "true"
        
        # Parse extracted_data if it's a JSON string
        if isinstance(extracted_data_param, str):
            full_data = json.loads(extracted_data_param)
        else:
            full_data = extracted_data_param
        
        print("FULL_DATA ---> ", full_data)
        
        # Determine the source of the data
        # Prioritize 'llm_response' as per latest structure
        data_source = full_data.get("llm_response") or full_data.get("extracted_data") or full_data
        
        # We try to find "milestones" list in the determined source
        milestones = data_source.get("milestones")
        
        if submit:
            if not milestones:
                frappe.throw("No milestones found in the extracted data.")
            print("MILESTONES ---> ", milestones)
            
            # Extract common data once
            matched_grant_info = data_source.get("matched_grant", {})
            matched_grant_id = matched_grant_info.get("grant_id")
            document_type = data_source.get("document_type")
            
            created_milestones = []
            for milestone in milestones:
                # Prepare dict for existing fields
                milestone_doc_data = {
                    "doctype": "Grant Project Milestone",
                    "title": (milestone.get("title") or "")[:100],
                    "project": milestone.get("project"),
                    "milestone_type": milestone.get("milestone_type"),
                    "submitted_at": milestone.get("submitted_at"),
                    "forecasted_amount": milestone.get("forecasted_amount"),
                    "period_start": milestone.get("period_start"),
                    "period_end": milestone.get("period_end"),
                    "metric_computed_at": milestone.get("metric_computed_at"),
                    "artifacts": milestone.get("artifacts", []),
                    "partners": milestone.get("partners", []),
                    "contributors": milestone.get("contributors", []),
                    "metrics_values": milestone.get("metrics_values", [])
                }
                
                # Check for required fields and try to auto-fix
                if not milestone_doc_data.get("title"):
                    milestone_doc_data["title"] = "Untitled Milestone"

                # Handle missing Project
                if not milestone_doc_data.get("project"):
                    # Try to resolve project from matched_grant_id
                    if matched_grant_id:
                        # Find the first project linked to this grant
                        projects = frappe.get_all("Grant Project", filters={"grant": matched_grant_id}, limit=1, ignore_permissions=True)
                        if projects:
                            milestone_doc_data["project"] = projects[0].name
                
                if not milestone_doc_data.get("project"):
                     # If still missing, we can't insert. Let it fail or throw a clear error?
                     # We'll fail at insert time, but let's provide a better error margin if possible or let frappe handle it.
                     pass
                milestone_doc_data["milestone_type"] = "Progress Update"
                # Handle missing Milestone Type
                if not milestone_doc_data.get("milestone_type"):
                    if document_type:
                        # Try to find exact match or case-insensitive match
                        if frappe.db.exists("Grant Project Milestone Type", document_type):
                            milestone_doc_data["milestone_type"] = document_type
                        else:
                            # Try to find something similar
                             similar = frappe.db.get_value("Grant Project Milestone Type", {"name": ["like", f"%{document_type}%"]})
                             if similar:
                                 milestone_doc_data["milestone_type"] = similar
                    
                    
                if not milestone_doc_data.get("milestone_type"):
                    # If still missing, pick the first available one as fallback
                    default_type = frappe.db.get_value("Grant Project Milestone Type")
                    if default_type:
                        milestone_doc_data["milestone_type"] = default_type
                
                # Resolve Child Table Links (Partners)
                # Extracted partners: [{ "partner": "Name", ... }, ...]
                # Target: "partner" field is Link to "Grant Partner", we need ID not Name/Title.
                processed_partners = []
                for p in milestone.get("partners", []):
                    partner_name_or_title = p.get("partner")
                    if not partner_name_or_title:
                        continue
                    
                    # Try to find ID
                    filters = {"title": partner_name_or_title}
                    if matched_grant_id:
                        filters["grant"] = matched_grant_id
                    
                    partner_id = frappe.db.get_value("Grant Partner", filters, "name")
                    if not partner_id and matched_grant_id:
                         # Try searching without strict grant filter just in case
                         partner_id = frappe.db.get_value("Grant Partner", {"title": partner_name_or_title}, "name")
                    
                    # If partner not found, create a new one
                    if not partner_id:
                        if matched_grant_id:
                            try:
                                new_partner = frappe.get_doc({
                                    "doctype": "Grant Partner",
                                    "grant": matched_grant_id,
                                    "title": partner_name_or_title
                                })
                                new_partner.insert(ignore_permissions=True)
                                partner_id = new_partner.name
                                print(f"Created new Grant Partner: '{partner_name_or_title}' ({partner_id})")
                            except Exception as e:
                                print(f"Error creating Grant Partner '{partner_name_or_title}': {str(e)}")
                                continue
                        else:
                            print(f"Warning: Cannot create Grant Partner '{partner_name_or_title}' - no grant ID available.")
                            continue
                    
                    processed_partners.append({
                        "doctype": "Grant Project Milestone Partner",
                        "partner": partner_id,
                        "responsibility": p.get("responsibility", ""),
                        "contributions": p.get("contributions", "")
                    })
                
                milestone_doc_data["partners"] = processed_partners

                # Process Child Table Records (Artifacts)
                # Extracted artifacts: [{ "link": "URL", "title": "...", "description": "..." }, ...]
                # Target: Each artifact needs "doctype" field
                processed_artifacts = []
                for artifact in milestone.get("artifacts", []):
                    artifact_link = artifact.get("link")
                    if not artifact_link:
                        print("Warning: Artifact missing required 'link' field, skipping.")
                        continue
                    
                    processed_artifacts.append({
                        "doctype": "Grant Project Milestone Artifact",
                        "link": artifact_link,
                        "title": artifact.get("title", ""),
                        "description": artifact.get("description", "")
                    })
                
                milestone_doc_data["artifacts"] = processed_artifacts

                # Resolve Child Table Links (Contributors)
                # Extracted contributors: [{ "team_member": "Name", ... }, ...]
                # Target: "team_member" field is Link to "Grant Member".
                processed_contributors = []
                for c in milestone.get("contributors", []):
                    member_name = c.get("team_member")
                    if not member_name:
                        continue
                        
                    filters = {"name1": member_name} # 'name1' is the field storing the name
                    if matched_grant_id:
                        filters["grant"] = matched_grant_id
                    
                    member_id = frappe.db.get_value("Grant Member", filters, "name")
                    if not member_id and matched_grant_id:
                        member_id = frappe.db.get_value("Grant Member", {"name1": member_name}, "name")

                    # If member not found, create a new one
                    if not member_id:
                        if matched_grant_id:
                            try:
                                # Use role from extracted data or default to 'Member'
                                designation = c.get("role") or "Member"
                                new_member = frappe.get_doc({
                                    "doctype": "Grant Member",
                                    "grant": matched_grant_id,
                                    "name1": member_name,
                                    "designation": designation
                                })
                                new_member.insert(ignore_permissions=True)
                                member_id = new_member.name
                                print(f"Created new Grant Member: '{member_name}' ({member_id})")
                            except Exception as e:
                                print(f"Error creating Grant Member '{member_name}': {str(e)}")
                                continue
                        else:
                            print(f"Warning: Cannot create Grant Member '{member_name}' - no grant ID available.")
                            continue
                    
                    processed_contributors.append({
                        "doctype": "Grant Project Milestone Contributor",
                        "team_member": member_id,
                        "role": c.get("role", "")
                    })
                
                milestone_doc_data["contributors"] = processed_contributors

                # Process Child Table Records (Metrics Values)
                # Extracted metrics_values: [{ "code": "...", "title": "...", "type": "INT", "value": 123 }, ...]
                # Target: Each metric value needs "doctype" field and value in correct data_* field
                processed_metrics = []
                for metric in milestone.get("metrics_values", []):
                    metric_code = metric.get("code")
                    metric_title = metric.get("title")
                    metric_type = metric.get("type", "").upper()
                    
                    if not metric_code or not metric_title or not metric_type:
                        print(f"Warning: Metric missing required fields (code, title, or type), skipping: {metric}")
                        continue
                    
                    # Validate type
                    if metric_type not in ["INT", "FLOAT", "BOOLEAN", "STRING"]:
                        print(f"Warning: Invalid metric type '{metric_type}', skipping: {metric}")
                        continue
                    
                    # Map value to appropriate field based on type
                    metric_record = {
                        "doctype": "Grant Metric Value",
                        "code": metric_code,
                        "title": metric_title,
                        "type": metric_type
                    }
                    
                    # Get the value from either 'value' or the specific data field
                    value = metric.get("value") or metric.get(f"data_{metric_type.lower()}")
                    
                    if value is not None:
                        if metric_type == "INT":
                            metric_record["data_int"] = int(value) if value else 0
                        elif metric_type == "FLOAT":
                            metric_record["data_float"] = float(value) if value else 0.0
                        elif metric_type == "BOOLEAN":
                            metric_record["data_boolean"] = bool(value) if value else False
                        elif metric_type == "STRING":
                            metric_record["data_string"] = str(value) if value else ""
                    
                    processed_metrics.append(metric_record)
                
                milestone_doc_data["metrics_values"] = processed_metrics

                # Insert document
                doc = frappe.get_doc(milestone_doc_data)
                doc.insert(ignore_permissions=True)
                created_milestones.append(doc.name)
                
                # Attach the file to this milestone if file_id is provided
                if file_id:
                    try:
                        # Get the file document
                        file_doc = frappe.get_doc("File", file_id)
                        
                        # Create a copy of the file attached to this milestone
                        attached_file = frappe.get_doc({
                            "doctype": "File",
                            "file_name": file_doc.file_name,
                            "file_url": file_doc.file_url,
                            "is_private": file_doc.is_private,
                            "attached_to_doctype": "Grant Project Milestone",
                            "attached_to_name": doc.name,
                            "attached_to_field": None
                        })
                        attached_file.insert(ignore_permissions=True)
                        print(f"Attached file {file_id} to milestone {doc.name}")
                    except Exception as e:
                        print(f"Warning: Failed to attach file to milestone {doc.name}: {str(e)}")

            frappe.db.commit()
            return {"status": "submitted", "created_milestones": created_milestones}
        else:
            # Discard/draft: acknowledge rejection
            return {"status": "rejected", "message": "Milestone data not saved."}
    except Exception as e:
        frappe.log_error(f"Error in submit_extracted_milestone: {str(e)}")
        frappe.response["http_status_code"] = 500
        error_msg = f"Error processing milestone: {str(e)}"
        print(f"\nERROR in submit_extracted_milestone: {error_msg}\n")
        frappe.throw(error_msg)
