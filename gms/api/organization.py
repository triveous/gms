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
