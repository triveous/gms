import frappe


def grant_has_permission(doc, user=None, ptype=None):
    if ptype == "create":
        return True

    if ptype in ("write", "delete"):
        org_member = get_organization_member()
        # Only admins of the funder organization can edit or delete the grant
        return (
            org_member
            and org_member.get("organization") == doc.funder
            and org_member.is_admin
        )

    return True


def grant_project_has_permission(doc, user=None, ptype=None):
    return True


def grant_project_milestone_has_permission(doc, user=None, ptype=None):
    return True


def grant_organization_has_permission(doc, user=None, ptype=None):
    return True


def grant_organization_member_has_permission(doc, user=None, ptype=None):
    return True


def get_organization_member(user: str = None) -> dict | None:
    if not user:
        user = frappe.session.user

    # Get from cache
    cache_key = f"aikam:organization_member:{user}"
    org_member = frappe.cache().get_value(cache_key)
    if org_member:
        return org_member

    # Get from DB and fill cache
    # We are not addingorg filter for organization here because we know a user can be member of only one organization
    org_member = frappe.db.get(
        "Grant Organization Member",
        filter={"user": user},
        as_dict=True,
        fields=["name", "user", "is_admin", "organization"],
    )

    if org_member:
        frappe.cache().set_value(cache_key, org_member)

    return org_member
