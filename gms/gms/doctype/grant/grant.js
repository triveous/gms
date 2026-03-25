// Copyright (c) 2025, Triveous and contributors
// For license information, please see license.txt

frappe.ui.form.on("Grant", {
	setup(frm) {
		// Enforce unique Grantee rule on the frontend by triggering a custom query
		// that filters out organizations already assigned to other grants.
		frm.set_query("organization", "contributors", function(doc, cdt, cdn) {
			let row = frappe.get_doc(cdt, cdn);
			if (row.contribution_type === "Grantee") {
				return {
					query: "gms.api.grant.get_grantee_organizations_query",
					filters: {
						grant: doc.name || ""
					}
				};
			}
			return {};
		});
	},
});

frappe.ui.form.on("Grant Contributor", {
	contribution_type: function(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		if (row.contribution_type === "Grantee") {
			// Trigger a refresh/re-evaluate on the field to apply the query instantly inside grid
			frm.fields_dict.contributors.grid.get_row(cdn).refresh_field("organization");
		}
	}
});
