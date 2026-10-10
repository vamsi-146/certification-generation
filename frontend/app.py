import os
import streamlit as st
import httpx
import pandas as pd

st.set_page_config(page_title="Bulk Certificate Generator", page_icon="🎓", layout="wide")


@st.dialog("Missing details")
def missing_dialog(fields):
    st.warning("Please fill in these fields in the sidebar before generating certificates:")
    for f in fields:
        st.write(f"- **{f}**")
    if st.button("OK", type="primary"):
        st.rerun()


st.title("🎓 Bulk Certificate Generator")

with st.sidebar:
    st.header("Configuration")
    api_base_url = st.text_input("API Base URL", value="http://localhost:8000")
    event_name = st.text_input("Event Name", placeholder="e.g. Python Workshop 2026")
    issuer = st.text_input("Issuer", placeholder="e.g. Tech Academy")
    date = st.text_input("Date", placeholder="e.g. October 10, 2026")

tab1, tab2 = st.tabs(["Generate Certificates", "Instructions"])

with tab1:
    st.header("Upload Recipients")

    upload_method = st.radio("Input Method", ["Upload CSV", "Paste Manually"])

    recipients_data = []

    if upload_method == "Upload CSV":
        uploaded_file = st.file_uploader("Upload CSV file (format: name,email - no header)", type=["csv"])

        if uploaded_file:
            try:
                # Read CSV without header
                df = pd.read_csv(uploaded_file, header=None, names=['name', 'email'])

                # Clean the data
                df = df.dropna()
                df['name'] = df['name'].str.strip()
                df['email'] = df['email'].str.strip()

                st.subheader("Preview")
                st.dataframe(df.head(10))
                st.write(f"Total recipients: {len(df)}")

                recipients_data = df.to_dict(orient='records')

            except Exception as e:
                st.error(f"Error reading file: {str(e)}")

    else:
        st.subheader("Paste Recipients")
        st.info("Enter one recipient per line in format: name,email")
        text_input = st.text_area("Recipients", height=200)

        if text_input:
            lines = text_input.strip().split('\n')

            for line in lines:
                parts = line.split(',')
                if len(parts) >= 2:
                    name = parts[0].strip()
                    email = parts[1].strip()
                    if name and email:
                        recipients_data.append({"name": name, "email": email})

            if recipients_data:
                st.subheader("Preview")
                st.dataframe(pd.DataFrame(recipients_data))
                st.write(f"Total recipients: {len(recipients_data)}")

    # Generate button (common for both methods)
    if recipients_data:
        st.divider()
        if st.button("Generate Certificates", type="primary", use_container_width=True):
            missing = [n for n, v in {"Event Name": event_name, "Issuer": issuer, "Date": date}.items() if not v.strip()]
            if missing:
                missing_dialog(missing)
            else:
                with st.spinner("Generating certificates..."):
                    payload = {
                        "event_name": event_name.strip(),
                        "issuer": issuer.strip(),
                        "date": date.strip(),
                        "recipients": recipients_data
                    }

                    try:
                        response = httpx.post(
                            f"{api_base_url}/api/jobs",
                            json=payload,
                            timeout=120.0
                        )

                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"Certificates generated for {len(result['certificates'])} recipients!")
                            st.session_state.generated_certificates = result['certificates']
                            st.rerun()
                        else:
                            st.error(f"Failed to generate certificates (Status {response.status_code}): {response.text}")
                    except httpx.TimeoutException:
                        st.error("Request timed out. Please try again.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # Show download options if certificates were generated
    if st.session_state.get('generated_certificates'):
        st.divider()
        st.subheader("Download Certificates")

        certificates = st.session_state.generated_certificates

        # Show results
        successful = [c for c in certificates if 'file_path' in c]
        failed = [c for c in certificates if 'error' in c]

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Successful", len(successful))
        with col2:
            st.metric("Failed", len(failed))

        if failed:
            st.error("Some certificates failed to generate:")
            for cert in failed:
                st.write(f"- {cert['name']}: {cert['error']}")

        if successful:
            st.subheader("Download Options")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Download All (ZIP)", type="primary"):
                    try:
                        zip_response = httpx.post(
                            f"{api_base_url}/api/jobs/download",
                            json=successful,
                            timeout=60.0
                        )

                        if zip_response.status_code == 200:
                            st.download_button(
                                label="Download ZIP",
                                data=zip_response.content,
                                file_name="certificates.zip",
                                mime="application/zip"
                            )
                        else:
                            st.error(f"Failed to download: {zip_response.text}")
                    except Exception as e:
                        st.error(f"Error downloading ZIP: {str(e)}")

            with col2:
                st.write("Individual Downloads:")
                for cert in successful:
                    try:
                        # Construct absolute path to the backend certificates directory
                        backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend', cert['file_path'])
                        with open(backend_path, 'rb') as f:
                            st.download_button(
                                label=f"{cert['name']}",
                                data=f.read(),
                                file_name=f"{cert['name']}.pdf",
                                mime="application/pdf",
                                key=cert['certificate_id']
                            )
                    except Exception as e:
                        st.error(f"Error loading {cert['name']}: {str(e)}")

with tab2:
    st.header("Instructions")

    st.markdown("""
    ## How to Use

    1. **Configure Event Details**: Use the sidebar to enter the event name, issuer, and date (all required).

    2. **Upload Recipients**:
       - Upload a CSV file with format: `name,email` (no header row)
       - Or paste recipients manually (one per line: `name,email`)

    3. **Generate Certificates**: Click the "Generate Certificates" button.

    4. **Download**:
       - Download all certificates as a ZIP file
       - Or download individual certificates by name

    ## CSV Format Example
    John Doe,john@example.com
    Jane Smith,jane@example.com



    ## Notes
    - Certificates are generated synchronously (wait for completion)
    - Generation may take time for large recipient lists
    - Failed certificates will show error messages
    """)