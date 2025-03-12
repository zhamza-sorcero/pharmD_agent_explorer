import streamlit as st
import pandas as pd
import requests
import json
import os
import re
import anthropic
from dotenv import load_dotenv
import base64
from pathlib import Path

# Import the ontology builder and profile generator from the existing code
from drug_ontology import DrugOntologyBuilder, DrugAssetProfileGenerator, generate_asset_markdown

# Custom function to add the sidebar logo and navigation
def add_sidebar_and_styling():
    # Add custom CSS for styling the sidebar and overall app appearance
    st.markdown("""
    <style>
        /* Main app background color and font */
        .stApp {
            background-color: #F8F9FA;
            font-family: 'Inter', sans-serif;
        }
        
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: white;
            border-right: 1px solid #EAEAEA;
            padding-top: 0;
        }
        
        /* Top company logo area in sidebar */
        .company-logo {
            padding: 20px 0;
            text-align: center;
            border-bottom: 1px solid #EAEAEA;
            margin-bottom: 20px;
        }
        
        /* Navigation items styling */
        .nav-item {
            display: flex;
            align-items: center;
            padding: 10px 20px;
            margin: 5px 0;
            border-radius: 5px;
            transition: background-color 0.3s;
            color: #444;
            text-decoration: none;
            font-weight: 500;
        }
        
        .nav-item:hover {
            background-color: #F0F2F5;
            cursor: pointer;
        }
        
        .nav-item.active {
            background-color: #F0F2F5;
            font-weight: bold;
            color: #111;
        }
        
        /* Icon styling within nav items */
        .nav-icon {
            margin-right: 10px;
            width: 24px;
            height: 24px;
            text-align: center;
        }
        
        /* Separator line */
        .separator {
            height: 1px;
            background-color: #EAEAEA;
            margin: 20px 0;
        }
        
        /* User profile area at bottom of sidebar */
        .user-profile {
            display: flex;
            align-items: center;
            padding: 15px 20px;
            border-top: 1px solid #EAEAEA;
            position: absolute;
            bottom: 0;
            width: 100%;
            background-color: white;
        }
        
        .user-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background-color: #EAEAEA;
            margin-right: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: #555;
        }
        
        .user-info {
            display: flex;
            flex-direction: column;
        }
        
        .user-name {
            font-weight: 600;
            font-size: 14px;
        }
        
        .user-email {
            font-size: 12px;
            color: #777;
        }
        
        /* Main content area styling */
        .main-content {
            padding: 20px 40px;
        }
        
        /* Input field styling */
        .stTextInput > div > div > input {
            padding: 10px 15px;
            font-size: 16px;
            border: 1px solid #EAEAEA;
            border-radius: 8px;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #6E7680;
            color: white;
            padding: 10px 20px;
            font-weight: 500;
            border-radius: 8px;
            border: none;
            transition: background-color 0.3s;
        }
        
        .stButton > button:hover {
            background-color: #5A6169;
        }
        
        /* Card styling for the form */
        .card {
            background-color: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        
        /* Back button styling */
        .back-button {
            display: inline-flex;
            align-items: center;
            color: #555;
            font-weight: 500;
            margin-bottom: 20px;
            cursor: pointer;
        }
        
        .back-icon {
            margin-right: 5px;
        }
    </style>
    """, unsafe_allow_html=True)

    
    # Company logo at the top of the sidebar
    st.sidebar.markdown('<div class="company-logo"><img src="https://s3.amazonaws.com/blab-impact-published-production/hLpfiMdVZIGcRiEjW6Yg1aP6qeI933uF" width="120"></div>', unsafe_allow_html=True)
    
    # Navigation items
    nav_items = [
        {"icon": "🏠", "label": "Home", "active": True},
        {"icon": "💡", "label": "Insights", "active": False},
        {"icon": "📄", "label": "Evidence", "active": False},
        {"icon": "🎯", "label": "Strategy", "active": False},
        {"icon": "📁", "label": "Collections", "active": False},
        {"icon": "📊", "label": "Reports", "active": False},
        {"icon": "🛠️", "label": "Tools", "active": False},
    ]
    
    for item in nav_items:
        active_class = "active" if item["active"] else ""
        st.sidebar.markdown(f'''
        <div class="nav-item {active_class}">
            <div class="nav-icon">{item["icon"]}</div>
            <div>{item["label"]}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    # Separator
    st.sidebar.markdown('<div class="separator"></div>', unsafe_allow_html=True)
    
    # Instant Insights
    st.sidebar.markdown(f'''
    <div class="nav-item">
        <div class="nav-icon">✨</div>
        <div>Instant Insights</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # User profile at the bottom
    st.sidebar.markdown(f'''
    <div class="user-profile">
        <div class="user-avatar">DD</div>
        <div class="user-info">
            <div class="user-name">Dipanwita Das</div>
            <div class="user-email">ddas@sorcero.com.com</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

# Function to get base64 encoded string for an image
def get_base64_of_image(image_path):
    """Get base64 encoded string for an image."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        # Return a placeholder or default value if image not found
        return ""

# Function to set page icon and config
def set_page_config():
    # Set page configuration with the logo as the icon
    st.set_page_config(
        page_title="PharmD Agent Explorer",
        page_icon="💊",
        layout="wide"
    )

# Function to fetch drug data from external APIs
def fetch_drug_data(drug_name):
    """Fetch real data for a drug from various APIs."""

    # Initialize data structure similar to mock data format
    data = {
        "fda_purple_book": {},
        "daily_med": {},
        "clinical_trials": [],
        "pubmed": []
    }

    # FDA Purple Book data
    try:
        # This is a placeholder - you would replace with actual FDA API endpoint
        fda_url = f"https://api.fda.gov/drug/drugsfda.json?search=openfda.generic_name:{drug_name}+OR+openfda.brand_name:{drug_name}"
        fda_response = requests.get(fda_url)

        if fda_response.status_code == 200:
            fda_data = fda_response.json()
            if 'results' in fda_data and len(fda_data['results']) > 0:
                result = fda_data['results'][0]

                # Extract relevant information
                brand_name = result.get('openfda', {}).get('brand_name', [drug_name.upper()])[
                    0] if 'openfda' in result else drug_name.upper()
                manufacturer = result.get('sponsor_name', 'Unknown Manufacturer')
                approval_date = result.get('products', [{}])[0].get('approval_date', 'Unknown') if len(
                    result.get('products', [])) > 0 else 'Unknown'
                application_number = result.get('application_number', 'Unknown')

                data["fda_purple_book"] = {
                    "source": "FDA Purple Book",
                    "text": f"{drug_name.upper()} - New Molecular Entity. Approved by FDA on {approval_date}. " +
                            f"Manufacturer: {manufacturer}. " +
                            f"BLA/NDA Number: {application_number}. " +
                            f"Current Regulatory Status: Approved.",
                    "metadata": {"drug_name": drug_name.lower(), "brand_name": brand_name}
                }
    except Exception as e:
        st.warning(f"Error fetching FDA data: {e}")

    # DailyMed data
    try:
        # Use DailyMed API to get data about the drug
        dailymed_url = f"https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json?drug_name={drug_name}"
        dailymed_response = requests.get(dailymed_url)

        if dailymed_response.status_code == 200:
            dailymed_data = dailymed_response.json()
            if 'data' in dailymed_data and len(dailymed_data['data']) > 0:
                # Get the set ID for the first result
                set_id = dailymed_data['data'][0].get('setid')

                # Fetch the full label using the set ID
                label_url = f"https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/{set_id}.json"
                label_response = requests.get(label_url)

                if label_response.status_code == 200:
                    label_data = label_response.json()

                    # Extract indications and usage
                    indications = "Indications not available."
                    mechanism = "Mechanism of action not available."

                    if 'data' in label_data and 'sections' in label_data['data']:
                        for section in label_data['data']['sections']:
                            if 'title' in section:
                                if 'INDICATIONS' in section['title'].upper() and 'USAGE' in section['title'].upper():
                                    indications = section.get('text', 'Indications not available.')
                                elif 'MECHANISM' in section['title'].upper() and 'ACTION' in section['title'].upper():
                                    mechanism = section.get('text', 'Mechanism of action not available.')

                    data["daily_med"] = {
                        "source": "DailyMed",
                        "text": f"{data['fda_purple_book'].get('metadata', {}).get('brand_name', drug_name.upper())} ({drug_name.lower()}) is a pharmaceutical agent indicated for: " +
                                indications + " " +
                                "Mechanism of Action: " + mechanism,
                        "metadata": {"drug_name": drug_name.lower(), "document_type": "label"}
                    }
    except Exception as e:
        st.warning(f"Error fetching DailyMed data: {e}")

    # ClinicalTrials.gov data
    try:
        # Use ClinicalTrials.gov API to get trial data
        ct_url = f"https://clinicaltrials.gov/api/query/full_studies?expr={drug_name}&min_rnk=1&max_rnk=10&fmt=json"
        ct_response = requests.get(ct_url)

        if ct_response.status_code == 200:
            ct_data = ct_response.json()
            if 'FullStudiesResponse' in ct_data and 'FullStudies' in ct_data['FullStudiesResponse']:
                for study in ct_data['FullStudiesResponse']['FullStudies']:
                    if 'Study' in study and 'ProtocolSection' in study['Study']:
                        protocol = study['Study']['ProtocolSection']

                        # Extract study information
                        trial_id = protocol.get('IdentificationModule', {}).get('NCTId', 'Unknown')
                        phase = protocol.get('DesignModule', {}).get('PhaseList', {}).get('Phase', ['Unknown'])[
                            0] if 'PhaseList' in protocol.get('DesignModule', {}) else 'Unknown'
                        description = protocol.get('DescriptionModule', {}).get('BriefSummary',
                                                                                'No description available.')
                        results = "Results not available."

                        # Check if results are available
                        if 'ResultsSection' in study['Study']:
                            results = "Results available. See ClinicalTrials.gov for details."

                        data["clinical_trials"].append({
                            "source": "ClinicalTrials.gov",
                            "trial_id": trial_id,
                            "text": f"Study {trial_id}: A {phase} study of " +
                                    f"{drug_name} in various conditions. " +
                                    f"Description: {description[:200]}... " +
                                    f"Results: {results}",
                            "metadata": {"drug_name": drug_name.lower(), "phase": phase if phase != 'Unknown' else ''}
                        })
    except Exception as e:
        st.warning(f"Error fetching clinical trials data: {e}")

    # PubMed data
    try:
        # Use PubMed API to get publication data
        pm_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={drug_name}&retmode=json&retmax=5"
        pm_response = requests.get(pm_url)

        if pm_response.status_code == 200:
            pm_data = pm_response.json()
            if 'esearchresult' in pm_data and 'idlist' in pm_data['esearchresult']:
                pmids = pm_data['esearchresult']['idlist']

                if pmids:
                    # Fetch details for each PubMed ID
                    pm_details_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={','.join(pmids)}&retmode=json"
                    pm_details_response = requests.get(pm_details_url)

                    if pm_details_response.status_code == 200:
                        pm_details_data = pm_details_response.json()

                        for pmid in pmids:
                            if pmid in pm_details_data.get('result', {}):
                                article = pm_details_data['result'][pmid]
                                title = article.get('title', 'No title available')
                                abstract = article.get('abstract', 'No abstract available')
                                year = article.get('pubdate', '').split()[0] if 'pubdate' in article else 'Unknown'

                                data["pubmed"].append({
                                    "source": "PubMed",
                                    "pmid": pmid,
                                    "text": f"{title}. " +
                                            f"Abstract: {abstract[:300]}...",
                                    "metadata": {"drug_name": drug_name.lower(), "publication_year": year}
                                })
    except Exception as e:
        st.warning(f"Error fetching PubMed data: {e}")

    # If we were unable to gather sufficient data, use Claude API to help fill in the gaps
    if (not data["fda_purple_book"] or
            not data["daily_med"] or
            len(data["clinical_trials"]) == 0 or
            len(data["pubmed"]) == 0):

        # Use Claude to augment missing data
        try:
            augmented_data = augment_drug_data_with_claude(drug_name, data)
            # Merge the augmented data with our existing data
            for key in data:
                if not data[key] and key in augmented_data:
                    data[key] = augmented_data[key]
                elif isinstance(data[key], list) and len(data[key]) == 0 and key in augmented_data:
                    data[key] = augmented_data[key]
        except Exception as e:
            st.warning(f"Error augmenting data with Claude: {e}")

    return data


def augment_drug_data_with_claude(drug_name, existing_data):
    """Use Claude API to fill in missing drug information."""

    api_key = st.secrets["ANTHROPIC_API_KEY"]
    client = anthropic.Anthropic(api_key=api_key)

    # Create a prompt that specifies what data we need
    prompt = f"""I need detailed, factual information about the drug {drug_name}. 
    Please provide information in the following format:

    1. FDA Purple Book information:
       - Approval date
       - Manufacturer
       - Brand name(s)
       - BLA/NDA number
       - Regulatory status

    2. Daily Med information:
       - Indications and usage
       - Mechanism of action

    3. Clinical Trials information (provide 2-3 key trials):
       - Trial ID
       - Phase
       - Study population
       - Key results
       - Safety information

    4. PubMed articles (provide 2-3 key publications):
       - PMID if known
       - Key findings about pharmacokinetics, pharmacodynamics, or clinical efficacy
       - Publication year

    Please be factual and specific. If certain information is not available or cannot be determined, please indicate that.
    """

    # Call Claude API
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=4000,
        temperature=0,
        system="You are a pharmaceutical information specialist with extensive knowledge of drugs, their approvals, mechanisms, clinical trials, and research literature. Provide only factual, accurate information. Be precise and detailed. Format as requested.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Parse the response
    content = response.content[0].text

    # Initialize the data structure
    augmented_data = {
        "fda_purple_book": {},
        "daily_med": {},
        "clinical_trials": [],
        "pubmed": []
    }

    # Extract FDA Purple Book data
    fda_match = re.search(r'FDA Purple Book information:(.*?)(?=\d+\.\s+Daily Med|$)', content, re.DOTALL)
    if fda_match and not existing_data.get("fda_purple_book"):
        fda_text = fda_match.group(1).strip()
        # Extract approval date
        approval_date_match = re.search(r'Approval date[:\s-]+(.+?)(?=\n|$)', fda_text, re.IGNORECASE)
        approval_date = approval_date_match.group(1).strip() if approval_date_match else "Unknown"
        # Extract manufacturer
        manufacturer_match = re.search(r'Manufacturer[:\s-]+(.+?)(?=\n|$)', fda_text, re.IGNORECASE)
        manufacturer = manufacturer_match.group(1).strip() if manufacturer_match else "Unknown"
        # Extract brand name
        brand_name_match = re.search(r'Brand name\(?s?\)?[:\s-]+(.+?)(?=\n|$)', fda_text, re.IGNORECASE)
        brand_name = brand_name_match.group(1).strip() if brand_name_match else drug_name.upper()
        # Extract BLA/NDA
        bla_match = re.search(r'BLA\/NDA(?:\s+number)?[:\s-]+(.+?)(?=\n|$)', fda_text, re.IGNORECASE)
        bla_number = bla_match.group(1).strip() if bla_match else "Unknown"
        # Extract regulatory status
        status_match = re.search(r'Regulatory status[:\s-]+(.+?)(?=\n|$)', fda_text, re.IGNORECASE)
        status = status_match.group(1).strip() if status_match else "Unknown"

        augmented_data["fda_purple_book"] = {
            "source": "FDA Purple Book",
            "text": f"{brand_name} ({drug_name}) - New Molecular Entity. Approved by FDA on {approval_date}. " +
                    f"Manufacturer: {manufacturer}. " +
                    f"BLA/NDA Number: {bla_number}. " +
                    f"Current Regulatory Status: {status}.",
            "metadata": {"drug_name": drug_name.lower(), "brand_name": brand_name}
        }

    # Extract Daily Med data
    daily_med_match = re.search(r'Daily Med information:(.*?)(?=\d+\.\s+Clinical Trials|$)', content, re.DOTALL)
    if daily_med_match and not existing_data.get("daily_med"):
        daily_med_text = daily_med_match.group(1).strip()
        # Extract indications
        indications_match = re.search(r'Indications and usage[:\s-]+(.+?)(?=Mechanism of action|$)', daily_med_text,
                                      re.DOTALL | re.IGNORECASE)
        indications = indications_match.group(1).strip() if indications_match else "Indications not available."
        # Extract mechanism
        mechanism_match = re.search(r'Mechanism of action[:\s-]+(.+?)(?=\n\d+\.|$)', daily_med_text,
                                    re.DOTALL | re.IGNORECASE)
        mechanism = mechanism_match.group(1).strip() if mechanism_match else "Mechanism of action not available."

        # Get brand name from FDA data or default to uppercase drug name
        brand_name = existing_data.get("fda_purple_book", {}).get("metadata", {}).get("brand_name", drug_name.upper())

        augmented_data["daily_med"] = {
            "source": "DailyMed",
            "text": f"{brand_name} ({drug_name.lower()}) is a pharmaceutical agent indicated for: " +
                    indications + " " +
                    "Mechanism of Action: " + mechanism,
            "metadata": {"drug_name": drug_name.lower(), "document_type": "label"}
        }

    # Extract Clinical Trials data
    ct_match = re.search(r'Clinical Trials information.*?:(.*?)(?=\d+\.\s+PubMed|$)', content, re.DOTALL)
    if ct_match and len(existing_data.get("clinical_trials", [])) == 0:
        ct_text = ct_match.group(1).strip()
        # Split by trial
        trial_blocks = re.split(r'(?:\n\s*-\s*Trial ID|\n\s*Trial \d+:)', ct_text)

        for i, block in enumerate(trial_blocks[1:], 1):
            trial_id_match = re.search(r'(?:Trial ID)?[:\s-]*(\w+\d+)', block, re.IGNORECASE)
            trial_id = trial_id_match.group(1).strip() if trial_id_match else f"Unknown-{i}"

            phase_match = re.search(r'Phase[:\s-]+(.+?)(?=\n|$)', block, re.IGNORECASE)
            phase = phase_match.group(1).strip() if phase_match else "Unknown"

            population_match = re.search(r'(?:Study )?[Pp]opulation[:\s-]+(.+?)(?=\n|$)', block, re.IGNORECASE)
            population = population_match.group(1).strip() if population_match else "Unknown population"

            results_match = re.search(r'Key results[:\s-]+(.+?)(?=Safety|$)', block, re.DOTALL | re.IGNORECASE)
            results = results_match.group(1).strip() if results_match else "Results not available."

            safety_match = re.search(r'Safety(?:\s+information)?[:\s-]+(.+?)(?=\n\n|$)', block,
                                     re.DOTALL | re.IGNORECASE)
            safety = safety_match.group(1).strip() if safety_match else "Safety information not available."

            augmented_data["clinical_trials"].append({
                "source": "ClinicalTrials.gov",
                "trial_id": trial_id,
                "text": f"Study {trial_id}: A {phase} study of {drug_name} in {population}. " +
                        f"Results: {results[:150]}... " +
                        f"Safety: {safety[:100]}...",
                "metadata": {"drug_name": drug_name.lower(), "phase": phase if phase != "Unknown" else ""}
            })

    # Extract PubMed data
    pubmed_match = re.search(r'PubMed articles.*?:(.*?)(?=$)', content, re.DOTALL)
    if pubmed_match and len(existing_data.get("pubmed", [])) == 0:
        pubmed_text = pubmed_match.group(1).strip()
        # Split by article
        article_blocks = re.split(r'(?:\n\s*-\s*PMID|\n\s*Article \d+:)', pubmed_text)

        for i, block in enumerate(article_blocks[1:], 1):
            pmid_match = re.search(r'(?:PMID)?[:\s-]*(\d+)', block, re.IGNORECASE)
            pmid = pmid_match.group(1).strip() if pmid_match else f"Unknown-{i}"

            findings_match = re.search(r'Key findings[:\s-]+(.+?)(?=Publication year|$)', block,
                                       re.DOTALL | re.IGNORECASE)
            findings = findings_match.group(1).strip() if findings_match else "Findings not available."

            year_match = re.search(r'Publication year[:\s-]+(.+?)(?=\n|$)', block, re.IGNORECASE)
            year = year_match.group(1).strip() if year_match else "Unknown"

            augmented_data["pubmed"].append({
                "source": "PubMed",
                "pmid": pmid,
                "text": findings[:300] + "...",
                "metadata": {"drug_name": drug_name.lower(), "publication_year": year}
            })

    return augmented_data


# Define the main app
def main():
    # Set page configuration
    set_page_config()
    
    # Add sidebar and styling
    add_sidebar_and_styling()
    
    # Main content area with back button if in results mode
    if st.session_state.get('results_displayed', False):
        st.markdown('<div class="back-button"><span class="back-icon">←</span> Back</div>', unsafe_allow_html=True)
    
    # App header
    st.markdown("<h1>PharmD Agent Explorer</h1>", unsafe_allow_html=True)
    st.markdown("<h3>Generate comprehensive markdown profiles for pharmaceutical assets using AI</h3>", unsafe_allow_html=True)

    # Add a sidebar option to clear results
    if st.session_state.get('results_displayed', False):
        if st.sidebar.button("Clear Results & Start New Search"):
            st.session_state.results_displayed = False
            st.session_state.drug_data = None
            st.session_state.profile = None
            st.session_state.visualization = None
            st.experimental_rerun()

    # If results are not displayed, show the input form
    if not st.session_state.get('results_displayed', False):
        # Create a card-like container for the form
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        # Put these titles inside the card to match the design
        st.markdown("<h2>Generate Asset Profile</h2>", unsafe_allow_html=True)
        st.markdown("<p>Enter the name of a pharmaceutical asset to generate a detailed markdown profile</p>", unsafe_allow_html=True)
        
        # Create a form with a more modern design
        col1, col2 = st.columns([4, 1])
        
        with col1:
            drug_name = st.text_input("", placeholder="Enter Asset name (e.g., Vivaflerud, ONCO-552)", label_visibility="collapsed")
            
        with col2:
            generate_button = st.button("Generate Profile", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        if generate_button and drug_name:
            with st.spinner(f"Generating profile for {drug_name}..."):
                # Fetch data for the specified drug
                drug_data = fetch_drug_data(drug_name)
                st.session_state.drug_data = drug_data

                # Initialize the drug profile generator
                profile_generator = DrugAssetProfileGenerator()

                # Generate the profile
                profile = profile_generator.generate_asset_profile(drug_name, drug_data)
                st.session_state.profile = profile

                # Generate visualization
                visualization = profile_generator.visualize_drug_ontology(drug_name,
                                                                          profile.get("Drug Ontology", {}))
                st.session_state.visualization = visualization

                # Generate markdown
                markdown_output = generate_asset_markdown(profile, visualization)
                st.session_state.markdown_output = markdown_output

                # Set flag to display results
                st.session_state.results_displayed = True

                # Rerun to refresh the UI
                st.experimental_rerun()

    # If results are available, display them
    else:
        if st.session_state.get('markdown_output'):
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(st.session_state.markdown_output, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Also add a button at the bottom to start a new search
            if st.button("Generate Another Profile"):
                st.session_state.results_displayed = False
                st.session_state.drug_data = None
                st.session_state.profile = None
                st.session_state.visualization = None
                st.experimental_rerun()


# Initialize session state if needed
if 'results_displayed' not in st.session_state:
    st.session_state.results_displayed = False

# Run the app
if __name__ == "__main__":
    main()
