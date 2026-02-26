import frappe
import json
import time
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
        from werkzeug.wrappers import Response
        from gms.ai.agents_v2.vercel_ui.stream_handler import VercelUIStreamHandler
        
        # Read file data
        file_content = file.read()
        
        # Task ID for tracking
        task_id = frappe.form_dict.get("task_id")
        
        # Save the uploaded file to Frappe's File doctype immediately
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file.filename,
            "is_private": 1,
            "content": file_content
        })
        file_doc.save(ignore_permissions=True)
        file_id = file_doc.name
        
        if task_id:
            frappe.db.set_value("Grant Document Extraction Task", task_id, {
                "uploaded_file": file_id,
                "uploaded_datetime": frappe.utils.now_datetime()
            })
            frappe.db.commit()

        def generator():
            handler = VercelUIStreamHandler()
            yield from handler.start()
            
            # Extract text from file based on format
            extracted_text = extract_text_from_file(file_content, file.filename)
            
            # Initialize classifier
            classifier = DocumentClassifier()
            
            if task_id:
                frappe.db.set_value("Grant Document Extraction Task", task_id, "status", "Extracting")
                frappe.publish_realtime("data-task", {"task": task_id, "status": "Extracting"})
                frappe.db.commit()
                yield from handler.write_task({"id": task_id, "status": "Extracting"})

            # STEP 1: Extraction
            extraction_result = classifier.extract_data(
                filename=file.filename,
                content=extracted_text,
                doc_id="uploaded_document"
            )
            
            if task_id:
                classifier.update_extraction_task(task_id, extraction_result)
            
            if task_id:
                frappe.db.set_value("Grant Document Extraction Task", task_id, {
                    "status": "Validating" if not extraction_result.get("isError") else "Extracting",
                    "raw_extraction_json": json.dumps(extraction_result) if not extraction_result.get("isError") else "{""}",
                    "extraction_error": json.dumps(extraction_result) if extraction_result.get("isError") else "{""}"
                })
                
                # Check for extraction error constraints (e.g., missing period, unknown projects)
                if extraction_result.get("isError"):
                    frappe.publish_realtime("data-task", {
                        "task": task_id, 
                        "status": "Extracting",
                        "isError": True,
                        "errorMessage": extraction_result.get("errorMessage")
                    })
                    frappe.db.commit()
                    yield from handler.write_task({
                        "id": task_id, 
                        "status": "extracting", 
                        "isError": True,
                        "errorMessage": extraction_result.get("errorMessage")
                    })
                    yield from handler.finish()
                    return

                frappe.publish_realtime("data-task", {"task": task_id, "status": "Validating"})
                frappe.db.commit()
                # Also send via SSE
                yield from handler.write_task({"id": task_id, "status": "Validating"})

            milestone_exists = classifier.check_milestone_exists(extraction_result)

            # STEP 2: Validation
            validation_result = classifier.validate_data(
                extracted_data=extraction_result,
                content=extracted_text,
                milestone_exists=milestone_exists
            )

            if task_id:
                frappe.db.set_value("Grant Document Extraction Task", task_id, {
                    "status": "Reviewing" if not validation_result.get("isError") else "Validating",
                    "raw_extraction_json": json.dumps(validation_result) if not validation_result.get("isError") else "{""}",
                    "extraction_error": json.dumps(validation_result) if validation_result.get("isError") else "{""}"
                })
                
                if validation_result.get("isError"):
                    frappe.publish_realtime("data-task", {
                        "task": task_id, 
                        "status": "Validating",
                        "isError": True,
                        "errorMessage": validation_result.get("errorMessage")
                    })
                    frappe.db.commit()
                    yield from handler.write_task({
                        "id": task_id, 
                        "status": "validating", 
                        "isError": True,
                        "errorMessage": validation_result.get("errorMessage")
                    })
                    yield from handler.finish()
                    return

                frappe.db.commit()


            classification_result = validation_result
            
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
                pass
            
            # Send final data-task with Reviewing status + llm_response + file_id
            # This replaces the old resume-data event and carries everything the UI needs
            # to open the ReviewDialog without a separate event type.
            yield from handler.write_task({
                "id": task_id,
                "status": "Reviewing",
                "llm_response": classification_result,
                "file_id": file_id,
                "filename": file.filename,
            })
            
            yield from handler.finish()


        return Response(
            generator(),
            status=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except Exception as e:
        frappe.log_error(f"Error in resume_with_file: {str(e)}")
        error_msg = f"Error processing file: {str(e)}"
        print(f"\nERROR in resume_with_file: {error_msg}\n")
        return Response(
            f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n",
            status=500,
            headers={"Content-Type": "text/event-stream"}
        )


@frappe.whitelist(allow_guest=True)
def submit_extracted_milestone():
    """API to accept submit/reject for extracted milestone data.
    Expects:
        - submit: true/false (boolean or string)
        - extracted_data: The classification result data (JSON string or dict)
        - file_id: ID of the uploaded file to attach to milestones
    """
    try:
        from werkzeug.wrappers import Response
        from gms.ai.agents_v2.vercel_ui.stream_handler import VercelUIStreamHandler

        def generator():
            handler = VercelUIStreamHandler()
            yield from handler.start()

            task_id = frappe.form_dict.get("task_id")
            # Send initial status
            yield from handler.write_task({"id": task_id, "status": "submitting"})

            try:
                submit = frappe.form_dict.get("submit")
                extracted_data_param = frappe.form_dict.get("extracted_data")
                file_id = frappe.form_dict.get("file_id")
                print("TASK ID:", task_id)
                if submit is None or extracted_data_param is None:
                    yield from handler.process_event("custom", {
                        "type": "error",
                        "message": "Missing required parameters: submit, extracted_data"
                    })
                    yield from handler.finish()
                    return

                # Parse boolean
                if isinstance(submit, str):
                    submit = submit.lower() == "true"
                
                # Parse extracted_data if it's a JSON string
                if isinstance(extracted_data_param, str):
                    full_data = json.loads(extracted_data_param)
                else:
                    full_data = extracted_data_param
                
                # Determine the source of the data
                data_source = full_data.get("llm_response") or full_data.get("extracted_data") or full_data
                
                # If task_id wasn't in form_dict, try to find it in the data payload
                if not task_id:
                    task_id = full_data.get("task_id") or full_data.get("task") or data_source.get("task_id") or data_source.get("task")

                print("TASK ID: ", task_id)
                milestones = data_source.get("milestones")
                timeline = data_source.get("timeline") or {} # Default to empty dict if missing
                
                if submit:
                    document_type = data_source.get("document_type")
                    
                    if document_type == "DPR":
                        created_docs = []
                        grant_details = data_source.get("grant_details", {})
                        projects_data = data_source.get("projects", [])
                        
                        # Process contributors
                        contributors = grant_details.get("contributors", [])
                        processed_contributors = []
                        for c in contributors:
                            org_name = c.get("organization_name")
                            if not org_name: continue
                            
                            org_id = frappe.db.get_value("Grant Organization", {"organization_name": org_name}, "name")
                            if not org_id:
                                try:
                                    new_org = frappe.get_doc({
                                        "doctype": "Grant Organization",
                                        "organization_name": org_name
                                    })
                                    new_org.insert(ignore_permissions=True)
                                    org_id = new_org.name
                                except Exception: continue
                            
                            processed_contributors.append({
                                "doctype": "Grant Contributor",
                                "organization": org_id,
                                "contribution_type": c.get("contribution_type") or "Funder"
                            })
                        
                        # Create Grant
                        grant_doc_data = {
                            "doctype": "Grant",
                            "title": grant_details.get("title") or "Untitled Grant",
                            "alias": grant_details.get("alias") or "UG",
                            "start_date": grant_details.get("start_date") or frappe.utils.nowdate(),
                            "end_date": grant_details.get("end_date"),
                            "approval_identifier": grant_details.get("approval_identifier") or "TBD",
                            "approved_amount": grant_details.get("approved_amount") or 0.0,
                            "contributors": processed_contributors
                        }
                        
                        grant_doc = frappe.get_doc(grant_doc_data)
                        grant_doc.insert(ignore_permissions=True)
                        grant_id = grant_doc.name
                        created_docs.append(grant_id)
                        
                        # Create Lead Organization Partner
                        lead_org_name = grant_details.get("lead_organization")
                        lead_partner_id = None
                        if lead_org_name:
                            try:
                                partner_doc = frappe.get_doc({
                                    "doctype": "Grant Partner",
                                    "grant": grant_id,
                                    "title": lead_org_name
                                })
                                partner_doc.insert(ignore_permissions=True)
                                lead_partner_id = partner_doc.name
                            except Exception: pass
                            
                            if lead_partner_id:
                                frappe.db.set_value("Grant", grant_id, "lead_organization", lead_partner_id)
                        
                        # Create Projects
                        for p in projects_data:
                            project_title = p.get("title")
                            if not project_title: continue
                            
                            p_lead_org = p.get("lead_organization")
                            p_partner_id = None
                            if p_lead_org:
                                p_partner_id = frappe.db.get_value("Grant Partner", {"title": p_lead_org, "grant": grant_id}, "name")
                                if not p_partner_id:
                                    try:
                                        new_p_partner = frappe.get_doc({
                                            "doctype": "Grant Partner",
                                            "grant": grant_id,
                                            "title": p_lead_org
                                        })
                                        new_p_partner.insert(ignore_permissions=True)
                                        p_partner_id = new_p_partner.name
                                    except Exception: pass
                                    
                            project_doc_data = {
                                "doctype": "Grant Project",
                                "grant": grant_id,
                                "title": project_title,
                                "alias": p.get("alias"),
                                "start_date": p.get("start_date"),
                                "end_date": p.get("end_date")
                            }
                            if p_partner_id:
                                project_doc_data["lead_organization"] = p_partner_id
                                
                            try:
                                proj_doc = frappe.get_doc(project_doc_data)
                                proj_doc.insert(ignore_permissions=True)
                                created_docs.append(proj_doc.name)
                            except Exception as e:
                                frappe.log_error(f"Failed to create Grant Project: {e}")
                                
                        # Attach file to Grant
                        if file_id:
                            try:
                                file_doc = frappe.get_doc("File", file_id)
                                attached_file = frappe.get_doc({
                                    "doctype": "File",
                                    "file_name": file_doc.file_name,
                                    "file_url": file_doc.file_url,
                                    "is_private": file_doc.is_private,
                                    "attached_to_doctype": "Grant",
                                    "attached_to_name": grant_id,
                                })
                                attached_file.insert(ignore_permissions=True)
                            except Exception: pass

                        frappe.db.commit()

                        if task_id:
                            frappe.db.set_value("Grant Document Extraction Task", task_id, "status", "Approved")
                            frappe.publish_realtime("data-task", {"task": task_id, "status": "Approved"})
                            frappe.db.commit()

                        yield from handler.write_task({"id": task_id, "status": "approved"})
                        yield from handler.process_event("custom", {
                            "type": "data-submit-result", 
                            "status": "submitted", 
                            "created_docs": created_docs
                        })

                    else:
                        if not milestones:
                            yield from handler.process_event("custom", {
                                "type": "error",
                                "message": "No milestones found in the extracted data."
                            })
                            yield from handler.finish()
                            return
                        
                        # Extract common data once
                        matched_grant_info = data_source.get("matched_grant", {})
                        matched_grant_id = matched_grant_info.get("grant_id")
                        
                        created_milestones = []
                        for milestone in milestones:
                            # Prepare dict for existing fields
                            milestone_doc_data = {
                                "doctype": "Grant Project Milestone",
                                "title": (milestone.get("title") or "")[:100],
                                "project": milestone.get("projectId"),
                                "milestone_type": milestone.get("milestone_type"),
                                "submitted_at": timeline.get("submitted_at"),
                                "forecasted_amount": milestone.get("forecasted_amount"),
                                "period_start": timeline.get("period_start"),
                                "period_end": timeline.get("period_end"),
                                "metric_computed_at": milestone.get("metric_computed_at"),
                                "artifacts": milestone.get("artifacts", []),
                                "partners": milestone.get("partners", []),
                                "contributors": milestone.get("contributors", []),
                                "metrics_values": milestone.get("metrics_values", [])
                            }
                            
                            if not milestone_doc_data.get("title"):
                                milestone_doc_data["title"] = "Untitled Milestone"
    
                            if not milestone_doc_data.get("project"):
                                if matched_grant_id:
                                    projects = frappe.get_all("Grant Project", filters={"grant": matched_grant_id}, limit=1, ignore_permissions=True)
                                    if projects:
                                        milestone_doc_data["project"] = projects[0].name
                            
                            milestone_doc_data["milestone_type"] = "Planning Update" if document_type == "YEARLY_PLAN" else "Progress Update"
                            
                            if not milestone_doc_data.get("milestone_type"):
                                if document_type:
                                    if frappe.db.exists("Grant Project Milestone Type", document_type):
                                        milestone_doc_data["milestone_type"] = document_type
                                    else:
                                        similar = frappe.db.get_value("Grant Project Milestone Type", {"name": ["like", f"%{document_type}%"]})
                                        if similar:
                                            milestone_doc_data["milestone_type"] = similar
                                
                            if not milestone_doc_data.get("milestone_type"):
                                default_type = frappe.db.get_value("Grant Project Milestone Type")
                                if default_type:
                                    milestone_doc_data["milestone_type"] = default_type
                            
                            # Resolve Partners
                            processed_partners = []
                            for p in milestone.get("partners", []):
                                partner_name_or_title = p.get("partner")
                                if not partner_name_or_title: continue
                                
                                partner_id = frappe.db.get_value("Grant Partner", {"title": partner_name_or_title, "grant": matched_grant_id} if matched_grant_id else {"title": partner_name_or_title}, "name")
                                
                                if not partner_id and matched_grant_id:
                                    try:
                                        new_partner = frappe.get_doc({
                                            "doctype": "Grant Partner",
                                            "grant": matched_grant_id,
                                            "title": partner_name_or_title
                                        })
                                        new_partner.insert(ignore_permissions=True)
                                        partner_id = new_partner.name
                                    except Exception: continue
                                
                                if partner_id:
                                    processed_partners.append({
                                        "doctype": "Grant Project Milestone Partner",
                                        "partner": partner_id,
                                        "responsibility": p.get("responsibility", ""),
                                        "contributions": p.get("contributions", "")
                                    })
                            milestone_doc_data["partners"] = processed_partners
    
                            # Process Artifacts
                            processed_artifacts = []
                            for artifact in milestone.get("artifacts", []):
                                artifact_link = artifact.get("link")
                                if not artifact_link: continue
                                processed_artifacts.append({
                                    "doctype": "Grant Project Milestone Artifact",
                                    "link": artifact_link,
                                    "title": artifact.get("title", ""),
                                    "description": artifact.get("description", "")
                                })
                            milestone_doc_data["artifacts"] = processed_artifacts
    
                            # Resolve Contributors
                            processed_contributors = []
                            for c in milestone.get("contributors", []):
                                member_name = c.get("team_member")
                                if not member_name: continue
                                    
                                filters = {"name1": member_name}
                                if matched_grant_id: filters["grant"] = matched_grant_id
                                member_id = frappe.db.get_value("Grant Member", filters, "name")
                                
                                if not member_id and matched_grant_id:
                                    try:
                                        new_member = frappe.get_doc({
                                            "doctype": "Grant Member",
                                            "grant": matched_grant_id,
                                            "name1": member_name,
                                            "designation": c.get("role") or "Member"
                                        })
                                        new_member.insert(ignore_permissions=True)
                                        member_id = new_member.name
                                    except Exception: continue
                                
                                if member_id:
                                    processed_contributors.append({
                                        "doctype": "Grant Project Milestone Contributor",
                                        "team_member": member_id,
                                        "role": "Member"
                                    })
                            milestone_doc_data["contributors"] = processed_contributors
    
                            # Process Metrics Values
                            processed_metrics = []
                            for metric in milestone.get("metrics_values", []):
                                metric_code = metric.get("code")
                                metric_title = metric.get("title")
                                metric_type = metric.get("type", "").upper()
                                
                                if not (metric_code and metric_title and metric_type) or metric_type not in ["INT", "FLOAT", "BOOLEAN", "STRING"]:
                                    continue
                                
                                metric_record = {
                                    "doctype": "Grant Metric Value",
                                    "code": metric_code,
                                    "title": metric_title,
                                    "type": metric_type
                                }
                                value = metric.get("value") or metric.get(f"data_{metric_type.lower()}")
                                if value is not None:
                                    field = f"data_{metric_type.lower()}"
                                    if metric_type == "INT": metric_record[field] = int(value)
                                    elif metric_type == "FLOAT": metric_record[field] = float(value)
                                    elif metric_type == "BOOLEAN": metric_record[field] = bool(value)
                                    elif metric_type == "STRING": metric_record[field] = str(value)
                                processed_metrics.append(metric_record)
                            milestone_doc_data["metrics_values"] = processed_metrics
    
                            # Insert document
                            doc = frappe.get_doc(milestone_doc_data)
                            doc.insert(ignore_permissions=True)
                            created_milestones.append(doc.name)
                            
                            if file_id:
                                try:
                                    file_doc = frappe.get_doc("File", file_id)
                                    attached_file = frappe.get_doc({
                                        "doctype": "File",
                                        "file_name": file_doc.file_name,
                                        "file_url": file_doc.file_url,
                                        "is_private": file_doc.is_private,
                                        "attached_to_doctype": "Grant Project Milestone",
                                        "attached_to_name": doc.name,
                                    })
                                    attached_file.insert(ignore_permissions=True)
                                except Exception: pass
    
                        frappe.db.commit()
    
                        if task_id:
                            frappe.db.set_value("Grant Document Extraction Task", task_id, "status", "Approved")
                            frappe.publish_realtime("data-task", {"task": task_id, "status": "Approved"})
                            frappe.db.commit()
    
                        # Send approved status after success (UI expects 'approved' to move to step 6)
                        yield from handler.write_task({"id": task_id, "status": "approved"})
                        yield from handler.process_event("custom", {
                            "type": "data-submit-result", 
                            "status": "submitted", 
                            "created_milestones": created_milestones
                        })
                else:
                    print("TASK ID: ", task_id)
                    # Discard/reject
                    if task_id:
                        frappe.db.set_value("Grant Document Extraction Task", task_id, "status", "Rejected")
                        frappe.publish_realtime("data-task", {"task": task_id, "status": "Rejected"})
                        frappe.db.commit()

                    # Notify UI of rejection
                    yield from handler.write_task({"id": task_id, "status": "rejected"})
                    yield from handler.process_event("custom", {
                        "type": "data-submit-result", 
                        "status": "rejected", 
                        "message": "Milestone data discarded."
                    })
                    time.sleep(0.2)
                    yield ":\n\n"   # SSE comment ping to force flush
                    

            except Exception as e:
                frappe.log_error(f"Error in submit_extracted_milestone generator: {str(e)}")
                yield from handler.process_event("custom", {
                    "type": "error",
                    "message": f"Error processing milestone: {str(e)}"
                })

            yield from handler.finish()

        return Response(
            generator(),
            status=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except Exception as e:
        frappe.log_error(f"Error in submit_extracted_milestone wrapper: {str(e)}")
        return Response(
            f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n",
            status=500,
            headers={"Content-Type": "text/event-stream"}
        )

