// Copyright (c) 2025, Triveous and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Grant Planning Form", {
// 	refresh(frm) {

// 	},
// });

frappe.realtime.on("progress", function (data) {
	frappe.show_progress(data.title || "Processing", data.perc, 100, data.description || "");
});
