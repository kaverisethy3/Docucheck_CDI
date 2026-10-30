import streamlit as st
import Database as database
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="DocuCheck CDI",
    page_icon="📋",
    layout="wide"
)

database.initialize_database()

if "patients" not in st.session_state:
    st.session_state.patients = [
        item["data"] for item in database.load_records("patient")
    ]

if "queries" not in st.session_state:
    st.session_state.queries = [
        item["data"] for item in database.load_records("query")
    ]

if "audit" not in st.session_state:
    st.session_state.audit = [
        item["data"] for item in database.load_records("audit")
    ]


def add_audit(action, case_id):
    event = {
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Action": action,
        "Case ID": case_id
    }
    st.session_state.audit.append(event)
    audit_key = datetime.now().strftime("%Y%m%d%H%M%S%f")
    database.save_record("audit", audit_key, event)


st.title("📋 DocuCheck CDI")
st.caption("Clinical Documentation Improvement Workbench — Educational demo using fictional data only.")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Documentation Gap Detection",
        "Query Management",
        "Coding Impact",
        "Audit Trail"
    ]
)

if page == "Dashboard":
    st.header("📊 Project Dashboard")

    patients = st.session_state.patients
    queries = st.session_state.queries

    col1, col2, col3 = st.columns(3)
    col1.metric("Cases Added", len(patients))
    col2.metric("Queries Created", len(queries))
    col3.metric(
        "Open Queries",
        sum(q.get("Status") == "Open" for q in queries)
    )

    st.subheader("📋 Documentation Quality")

    if patients:
        gap_cases = sum(
            p.get("Potential Gaps", "None flagged") not in
            ["None flagged", "", None]
            for p in patients
        )
        st.metric("Cases with Potential Gaps", gap_cases)
        st.caption("Potential gaps require human review.")
    else:
        st.info("Add a fictional case to see documentation quality.")

    st.subheader("📝 Specialty-wise Query Volume")

    if queries:
        query_rows = []

        for q in queries:
            case = next(
                (
                    p for p in patients
                    if p.get("Case ID") == q.get("Case ID")
                ),
                {}
            )

            query_rows.append({
                "Specialty": case.get("Specialty", "Not recorded"),
                "Query ID": q.get("Query ID", ""),
                "Status": q.get("Status", "Open"),
                "Response Time (hours)": q.get("Response Time (hours)"),
                "Accepted": q.get("Accepted")
            })

        query_df = pd.DataFrame(query_rows)

        specialty_summary = (
            query_df.groupby("Specialty")
            .size()
            .reset_index(name="Query Volume")
        )
        st.dataframe(specialty_summary, use_container_width=True)

        st.subheader("Query Status Summary")
        status_summary = (
            query_df.groupby("Status")
            .size()
            .reset_index(name="Count")
        )
        st.dataframe(status_summary, use_container_width=True)

        answered = [
            q for q in queries
            if q.get("Response Time (hours)") is not None
        ]

        accepted = [
            q for q in queries
            if q.get("Accepted") is True or q.get("Accepted") is False
        ]

        col1, col2 = st.columns(2)

        if answered:
            average = sum(
                q["Response Time (hours)"] for q in answered
            ) / len(answered)
            col1.metric("Average Response Time", f"{average:.2f} hours")
        else:
            col1.metric("Average Response Time", "Not recorded")

        if accepted:
            rate = sum(
                q.get("Accepted") is True for q in accepted
            ) / len(accepted) * 100
            col2.metric("Acceptance Rate", f"{rate:.1f}%")
        else:
            col2.metric("Acceptance Rate", "Not recorded")

        st.caption(
            "SLA target must be set by the project supervisor. "
            "Response-time figures depend on recorded data."
        )
    else:
        st.info("Create a query to view query volume and performance.")

    st.subheader("Compliance and Financial Impact")
    st.write(
        "Use human review and an audit trail to support compliance. "
        "Actual financial impact is not calculated because validated "
        "coding and reimbursement data has not been supplied."
    )


elif page == "Documentation Gap Detection":
    st.header("🔎 Documentation Gap Detection")
    st.write("Enter a fictional case for a documentation review.")

    with st.form("case_form"):
        case_id = st.text_input("Case ID")
        specialty = st.selectbox(
            "Specialty",
            ["General Medicine", "Cardiology", "Orthopedics",
             "Neurology", "Other"]
        )
        condition = st.text_input("Documented condition")

        laterality = st.selectbox(
            "Laterality",
            ["Not applicable", "Documented", "Not documented", "Unclear"]
        )
        acuity = st.selectbox(
            "Acuity",
            ["Not applicable", "Documented", "Not documented", "Unclear"]
        )
        stage = st.selectbox(
            "Stage",
            ["Not applicable", "Documented", "Not documented", "Unclear"]
        )
        etiology = st.selectbox(
            "Etiology",
            ["Not applicable", "Documented", "Not documented", "Unclear"]
        )

        case_submitted = st.form_submit_button("Save Case")

    if case_submitted:
        if not case_id.strip() or not condition.strip():
            st.error("Enter both Case ID and documented condition.")
        elif any(
            p.get("Case ID", "").lower() == case_id.strip().lower()
            for p in st.session_state.patients
        ):
            st.error("This Case ID already exists.")
        else:
            fields = {
                "Laterality": laterality,
                "Acuity": acuity,
                "Stage": stage,
                "Etiology": etiology
            }

            priorities = {
                "Laterality": "High",
                "Acuity": "High",
                "Stage": "Medium",
                "Etiology": "High"
            }

            gaps = [
                name for name, value in fields.items()
                if value in ["Not documented", "Unclear"]
            ]

            priority_gaps = [
                f"{gap} ({priorities[gap]})" for gap in gaps
            ]

            record = {
                "Case ID": case_id.strip(),
                "Specialty": specialty,
                "Condition": condition.strip(),
                **fields,
                "Potential Gaps": ", ".join(gaps) if gaps else "None flagged",
                "Gap Priority": ", ".join(priority_gaps) if priority_gaps else "None",
                "Review Date": datetime.now().strftime("%Y-%m-%d %H:%M")
            }

            st.session_state.patients.append(record)
            database.save_record("patient", record["Case ID"], record)
            add_audit("Case created", record["Case ID"])
            st.success("Case saved successfully!")

            if gaps:
                st.warning("Potential gaps: " + ", ".join(gaps))
            else:
                st.info("No potential gaps flagged by these fields.")

    if st.session_state.patients:
        st.subheader("Saved Cases")
        st.dataframe(
            pd.DataFrame(st.session_state.patients),
            use_container_width=True
        )


elif page == "Query Management":
    st.header("📝 Provider Query Management")
    st.caption("Use neutral questions and fictional demonstration data.")

    if not st.session_state.patients:
        st.info("First add a case under Documentation Gap Detection.")
    else:
        case_ids = [
            p["Case ID"] for p in st.session_state.patients
        ]

        with st.form("query_form"):
            selected_case = st.selectbox("Select Case ID", case_ids)
            topic = st.text_input("Clarification topic")
            clinical_context = st.text_area(
                "Relevant documented clinical indicators"
            )
            question = st.text_area(
                "Neutral provider question",
                placeholder="Please clarify the clinical documentation based on the information provided."
            )
            query_submitted = st.form_submit_button("Create Query")

        if query_submitted:
            if (
                not topic.strip()
                or not clinical_context.strip()
                or not question.strip()
            ):
                st.error("Complete all query fields.")
            else:
                query_id = f"Q-{int(datetime.now().timestamp() * 1000)}"

                record = {
                    "Query ID": query_id,
                    "Case ID": selected_case,
                    "Topic": topic.strip(),
                    "Clinical Indicators": clinical_context.strip(),
                    "Question": question.strip(),
                    "Status": "Open",
                    "Created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Response Time (hours)": None,
                    "Accepted": None
                }

                st.session_state.queries.append(record)
                database.save_record("query", query_id, record)
                add_audit(f"Query created: {query_id}", selected_case)
                st.success(f"Query {query_id} created successfully!")

    if st.session_state.queries:
        st.subheader("Update Query Status")

        query_ids = [
            q["Query ID"] for q in st.session_state.queries
        ]

        with st.form("update_query_form"):
            selected_query = st.selectbox("Choose query", query_ids)
            new_status = st.selectbox(
                "New status",
                ["Open", "Answered", "Escalated", "Closed"]
            )
            acceptance = st.selectbox(
                "Was the clarification accepted?",
                ["Not recorded", "Yes", "No"]
            )
            update_submitted = st.form_submit_button("Update Query")

        if update_submitted:
            query = next(
                (
                    q for q in st.session_state.queries
                    if q["Query ID"] == selected_query
                ),
                None
            )

            if query:
                old_status = query.get("Status", "Open")
                query["Status"] = new_status

                if (
                    new_status in ["Answered", "Closed"]
                    and acceptance != "Not recorded"
                ):
                    query["Accepted"] = acceptance == "Yes"

                if (
                    new_status in ["Answered", "Closed"]
                    and query.get("Response Time (hours)") is None
                ):
                    created_text = query.get("Created")

                    if created_text:
                        try:
                            created_time = datetime.strptime(
                                created_text, "%Y-%m-%d %H:%M"
                            )
                            elapsed = (
                                datetime.now() - created_time
                            ).total_seconds() / 3600
                            query["Response Time (hours)"] = round(
                                max(0, elapsed), 2
                            )
                        except ValueError:
                            pass

                database.save_record(
                    "query", query["Query ID"], query
                )
                add_audit(
                    f"{selected_query}: {old_status} → {new_status}",
                    query.get("Case ID", "")
                )
                st.success("Query updated successfully!")

        st.subheader("All Queries")
        st.dataframe(
            pd.DataFrame(st.session_state.queries),
            use_container_width=True
        )


elif page == "Coding Impact":
    st.header("📈 Coding Impact Reconciliation")
    st.caption(
        "Educational example only. No real medical codes or "
        "reimbursement amounts are calculated."
    )

    if not st.session_state.patients:
        st.info("Add a fictional case first.")
    else:
        case_ids = [
            p["Case ID"] for p in st.session_state.patients
        ]

        with st.form("impact_form"):
            impact_case = st.selectbox("Case ID", case_ids)
            before = st.text_input("Pre-clarification coding summary")
            after = st.text_input("Post-clarification coding summary")
            note = st.text_input("Impact note (optional)")
            impact_submitted = st.form_submit_button("Save Reconciliation")

        if impact_submitted:
            if not before.strip() or not after.strip():
                st.error("Enter both pre- and post-clarification summaries.")
            else:
                action = (
                    f"Reconciliation saved. Before: {before.strip()}; "
                    f"After: {after.strip()}; Note: {note.strip()}"
                )
                add_audit(action, impact_case)
                st.success("Reconciliation saved to the audit trail.")

    saved_audits = database.load_records("audit")
    reconciliations = [
        item["data"] for item in saved_audits
        if item["key"].startswith("reconciliation_")
    ]

    if reconciliations:
        st.subheader("Saved Reconciliation History")
        for item in reversed(reconciliations):
            st.write("**Case ID:**", item.get("Case ID", "N/A"))
            st.write("**Time:**", item.get("Time", "N/A"))
            st.write("**Details:**", item.get("Action", "N/A"))
            st.divider()
    else:
        st.info(
            "No separately keyed reconciliation records found. "
            "New reconciliation entries are available in the audit trail."
        )


elif page == "Audit Trail":
    st.header("🧾 Audit Trail")

    saved_audits = database.load_records("audit")
    audit_rows = [item["data"] for item in saved_audits]

    if audit_rows:
        st.dataframe(
            pd.DataFrame(audit_rows),
            use_container_width=True
        )
    else:
        st.info("No audit events recorded yet.")