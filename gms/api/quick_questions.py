import frappe


@frappe.whitelist(allow_guest=True)
def get_all_quick_questions():
    questions = frappe.get_all(
        "Quick Question",
        fields=["name", "question", "creation"],
        order_by="creation desc",
    )

    return {
        "count": len(questions),
        "questions": questions,
    }