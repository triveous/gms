import frappe


def grant_has_permission(doc, user=None, ptype=None):
    """
    User permission will be checked as per below rules and when this return true, role based permission will be checked next.:
    1. Any user who is part of an organization can create a grant.
    2. Members of any contributing organization can read/write the grant.
    3. Only Member of funding organization can delete the grant.
    """
    if ptype == "create":
        org_user = get_organization_user(user)
        return org_user is not None

    if ptype in ("read", "write"):
        org_user = get_organization_user(user)
        contributing_org = [d.get("organization") for d in doc.contributors]
        # Members of any contributing organization can read/write the grant
        return (
            org_user is not None
            and contributing_org
            and org_user.get("organization") in contributing_org
        )

    if ptype == "delete":
        org_user = get_organization_user(user)
        # Members of funding organization can delete the grant
        funding_org = [
            d.get("organization")
            for d in doc.contributors
            if d.get("contribution_type") == "Funder"
        ]
        print(org_user)
        print(funding_org)
        return (
            org_user is not None
            and org_user.get("is_admin")
            and org_user.get("organization") in funding_org
        )

    return False


def grant_project_has_permission(doc, user=None, ptype=None):
    """
    User permission will be checked as per below rules and when this return true, role based permission will be checked next.:
    1. Only Grantee Organizations can create/read/update/delete grant projects.
    """
    contributors = frappe.db.get_all(
        "Grant Contributor",
        {"parent": doc.grant},
        ["organization", "contribution_type"],
    )

    if ptype in ("create", "read", "write", "delete"):
        org_user = get_organization_user(user)
        print(contributors)
        print(org_user)
        grantee_org = [
            d.get("organization")
            for d in contributors
            if d.get("contribution_type") == "Grantee"
        ]
        # Members of grantee organization can create/read/update/delete the grant project
        return (
            org_user is not None
            and grantee_org
            and org_user.get("organization") in grantee_org
        )
    return False


def grant_project_milestone_has_permission(doc, user=None, ptype=None):
    """
    User permission will be checked as per below rules and when this return true, role based permission will be checked next.:
    1. Only Grantee Organizations can create/read/update/delete grant projects milestone.
    """
    grant = frappe.db.get_value("Grant Project", doc.project, "grant")
    contributors = frappe.db.get_all(
        "Grant Contributor",
        {"parent": grant},
        ["organization", "contribution_type"],
    )

    if ptype in ("create", "read", "write", "delete"):
        org_user = get_organization_user(user)
        grantee_org = [
            d.get("organization")
            for d in contributors
            if d.get("contribution_type") == "Grantee"
        ]
        # Members of any contributing organization can read the grant
        return (
            org_user is not None
            and grantee_org
            and org_user.get("organization") in grantee_org
        )
    return False


def grant_organization_user_has_permission(doc, user=None, ptype=None):
    """
    User permission will be checked as per below rules and when this return true, role based permission will be checked next.:
    1. Only admin of that organization can create/read/update/delete Grant Organization User.
    """
    if ptype in ("create", "read", "write", "delete"):
        org_user = get_organization_user(user)
        return (
            org_user is not None
            and org_user.get("is_admin")
            and org_user.get("organization") == doc.organization
        )
    return False


def grant_query(user):
    org_user = get_organization_user(user)
    if org_user is None:
        return ""
    org = org_user.get("organization")
    return f"name IN (select parent from `tabGrant Contributor` where `tabGrant Contributor`.organization={frappe.db.escape(org)})"


def grant_project_query(user):
    org_user = get_organization_user(user)
    if org_user is None:
        return ""
    org = org_user.get("organization")
    return f"`tabGrant Project`.grant IN (select parent from `tabGrant Contributor` where `tabGrant Contributor`.organization={frappe.db.escape(org)})"


def grant_project_milestone_query(user):
    org_user = get_organization_user(user)
    if org_user is None:
        return ""

    projects = frappe.get_list(
        "Grant Project",
        fields=["name"],
    )
    project_names = [frappe.db.escape(project.name) for project in projects]
    return f"`tabGrant Project Milestone`.project in ({', '.join(project_names)})"


def grant_organization_user_query(user):
    org_user = get_organization_user(user)
    if org_user is None:
        return ""
    org = org_user.get("organization")
    return f"organization={frappe.db.escape(org)}"


def ai_conversation_query(user):
    if not user or user == "Guest":
        return "1=0"
    return f"owner = {frappe.db.escape(user)}"


def get_organization_user(user: str = None) -> dict | None:
    if not user:
        user = frappe.session.user

    if not user or user == "Guest":
        return None

    # Get from cache
    cache_key = f"gms:organization_userqoll:{user}"
    org_user = frappe.cache().get_value(cache_key, expires=300)
    if org_user:
        return org_user

    # Get from DB and fill cache
    # We are not addingorg filter for organization here because we know a user can be member of only one organization
    org_user = frappe.db.get(
        "Grant Organization User",
        {"user": user},
        ["name", "user", "is_admin", "organization"],
    )

    if org_user:
        frappe.cache().set_value(cache_key, org_user)

    return org_user
