import frappe


@frappe.whitelist()
def get_user_organization():
	"""
	Fetch organization details for a given user ID from grant_organization_user.
	
	Parameters:
	- user_id: User ID to lookup
	
	Returns: {organization, organization_name, user, is_admin} or error if not found
	"""
	try:
		user = frappe.session.user
		# Fetch the grant_organization_user record for the current session user
		org_user = frappe.get_list(
			"Grant Organization User",
			fields=["organization", "user", "is_admin"],
			filters={"user": user},
			limit_page_length=1,
		)

		if not org_user:
			return None
		
		org_user_data = org_user[0]
		organization_id = org_user_data.get("organization")
		
		# Fetch organization details
		organization = frappe.get_doc("Grant Organization", organization_id)
		
		if not organization:
			frappe.throw("Organization not found")
		
		return {
			"organization": organization_id,
			"organization_name": organization.organization_name,
			"user": org_user_data.get("user"),
			"is_admin": org_user_data.get("is_admin"),
		}
		

	except Exception as e:
		frappe.throw(f"Error fetching organization: {str(e)}")


@frappe.whitelist()
def get_user_grantee_grant():
	"""
	Check if the current session user belongs to an organization that is
	a 'Grantee' in any grant's contributors table.

	Returns: {"grant_id": <grant_id>} or {"grant_id": null}
	"""
	try:
		user = frappe.session.user

		# Step 1: Get user's organization from Grant Organization User
		org_users = frappe.get_list(
			"Grant Organization User",
			fields=["organization"],
			filters={"user": user},
			limit_page_length=1,
		)

		if not org_users:
			return {"grant_id": None}

		organization = org_users[0].get("organization")
		if not organization:
			return {"grant_id": None}

		# Step 2: Check if this organization is a Grantee in any Grant's contributors
		grantee_entries = frappe.get_all(
			"Grant Contributor",
			fields=["parent"],
			filters={
				"organization": organization,
				"contribution_type": "Grantee",
			},
			limit_page_length=1,
		)

		if not grantee_entries:
			return {"grant_id": None}

		grant_id = grantee_entries[0].get("parent")
		return {"grant_id": grant_id}

	except Exception as e:
		frappe.log_error(f"Error in get_user_grantee_grant: {str(e)}")
		return {"grant_id": None}
