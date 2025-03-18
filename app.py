import streamlit as st
import requests
import json
import re
import copy
import traceback
import base64
from dotenv import load_dotenv

# Import the ontology builder and profile generator
from drug_ontology import DrugOntologyBuilder, DrugAssetProfileGenerator, generate_asset_markdown, generate_enhanced_asset_markdown

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
            padding: 3px 7px;
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
    st.sidebar.markdown(
        '<div class="company-logo"><img src="https://s3.amazonaws.com/blab-impact-published-production/hLpfiMdVZIGcRiEjW6Yg1aP6qeI933uF" width="120"></div>',
        unsafe_allow_html=True)

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

    # User profile at the bottom
    st.sidebar.markdown(f'''
    <div class="user-profile">
        <div class="user-avatar">DD</div>
        <div class="user-info">
            <div class="user-name">Dipanwita Das</div>
            <div class="user-email">ddas@sorcero.com</div>
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

# Load environment variables
load_dotenv()


# Function to fetch drug data from external APIs
def fetch_drug_data(drug_name):
    """Fetch comprehensive data for a drug from various APIs with enhanced error handling."""

    # Initialize data structure
    data = {
        "fda_purple_book": {},
        "daily_med": {},
        "clinical_trials": [],
        "pubmed": []
    }

    # Track if we need Claude augmentation
    missing_data = False

    # Track which data sources were successfully queried
    successful_sources = []

    # FDA Purple Book data - using openFDA API
    try:
        # Use the improved openFDA API call
        fda_data = fetch_openfda_data(drug_name)

        if fda_data and fda_data.get("drug_info"):
            # Extract relevant information from structured response
            drug_info = fda_data.get("drug_info", {})
            latest_submission = drug_info.get("latest_submission", {})

            # Get product info
            products = drug_info.get("products", [])
            product_info = products[0] if products else {}

            # Extract key data points
            brand_name = product_info.get("brand_name", drug_name.upper())
            manufacturer = drug_info.get("sponsor_name", "Unknown Manufacturer")
            approval_date = latest_submission.get("submission_status_date", "Unknown")
            application_number = drug_info.get("application_number", "Unknown")

            data["fda_purple_book"] = {
                "source": "FDA Purple Book",
                "text": f"{brand_name} - New Molecular Entity. Approved by FDA on {approval_date}. " +
                        f"Manufacturer: {manufacturer}. " +
                        f"BLA/NDA Number: {application_number}. " +
                        f"Current Regulatory Status: {latest_submission.get('submission_status', 'Approved')}.",
                "metadata": {"drug_name": drug_name.lower(), "brand_name": brand_name}
            }
            successful_sources.append("FDA")
        else:
            # Fallback to original FDA API method
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
                        "text": f"{brand_name} - New Molecular Entity. Approved by FDA on {approval_date}. " +
                                f"Manufacturer: {manufacturer}. " +
                                f"BLA/NDA Number: {application_number}. " +
                                f"Current Regulatory Status: Approved.",
                        "metadata": {"drug_name": drug_name.lower(), "brand_name": brand_name}
                    }
                    successful_sources.append("FDA")
                else:
                    missing_data = True
                    #st.warning("Limited FDA data found.")
            else:
                missing_data = True
                #st.warning(f"Could not fetch FDA data (Status: {fda_response.status_code}).")
    except Exception as e:
        missing_data = True
        #st.warning(f"Error fetching FDA data: {str(e)}.")

    # DailyMed data with enhanced parsing
    try:
        # First try DailyMed API to get basic data
        dailymed_url = f"https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json?drug_name={drug_name}"

        # Add specific headers that DailyMed expects
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'PharmDExplorer/1.0 (research application; contact@example.com)'
        }

        dailymed_response = requests.get(dailymed_url, headers=headers)

        if dailymed_response.status_code == 200:
            dailymed_data = dailymed_response.json()
            if 'data' in dailymed_data and len(dailymed_data['data']) > 0:
                # Get the set ID for the first result
                set_id = dailymed_data['data'][0].get('setid')

                # Fetch the full label using the set ID
                label_url = f"https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/{set_id}.json"
                label_response = requests.get(label_url, headers=headers)

                if label_response.status_code == 200:
                    label_data = label_response.json()

                    # Extract indications and usage with improved parsing
                    indications = "Indications not available."
                    mechanism = "Mechanism of action not available."

                    if 'data' in label_data and 'sections' in label_data['data']:
                        for section in label_data['data']['sections']:
                            if 'title' in section:
                                # More flexible matching for indications section
                                if any(term in section['title'].upper() for term in ['INDICATIONS', 'USAGE', 'USES']):
                                    indications = section.get('text', 'Indications not available.')
                                # More flexible matching for mechanism section
                                elif any(term in section['title'].upper() for term in
                                         ['MECHANISM', 'ACTION', 'PHARMACOLOGY', 'HOW IT WORKS']):
                                    mechanism = section.get('text', 'Mechanism of action not available.')
                                # Look in clinical pharmacology section as fallback for mechanism
                                elif 'CLINICAL PHARMACOLOGY' in section['title'].upper():
                                    if mechanism == "Mechanism of action not available.":
                                        mechanism = section.get('text', 'Mechanism of action not available.')

                    # Try to use openFDA label data if available as a supplementary source
                    if fda_data and fda_data.get("label_info"):
                        label_info = fda_data.get("label_info", {})

                        # If we didn't find indications, check openFDA
                        if indications == "Indications not available.":
                            fda_indications = label_info.get("indications_usage", ["Indications not available."])
                            if fda_indications and fda_indications[0] != "Not available":
                                indications = " ".join(fda_indications)

                        # If we didn't find mechanism, check openFDA
                        if mechanism == "Mechanism of action not available.":
                            fda_mechanism = label_info.get("mechanism_of_action",
                                                           ["Mechanism of action not available."])
                            if fda_mechanism and fda_mechanism[0] != "Not available":
                                mechanism = " ".join(fda_mechanism)
                            else:
                                # Try clinical pharmacology section as fallback
                                fda_pharmacology = label_info.get("clinical_pharmacology", ["Not available"])
                                if fda_pharmacology and fda_pharmacology[0] != "Not available":
                                    mechanism = " ".join(fda_pharmacology)

                    # Get the appropriate brand name
                    brand_name = data.get('fda_purple_book', {}).get('metadata', {}).get('brand_name',
                                                                                         drug_name.upper())

                    data["daily_med"] = {
                        "source": "DailyMed",
                        "text": f"{brand_name} ({drug_name.lower()}) is a pharmaceutical agent indicated for: " +
                                indications + " " +
                                "Mechanism of Action: " + mechanism,
                        "metadata": {"drug_name": drug_name.lower(), "document_type": "label"}
                    }
                    successful_sources.append("DailyMed")
                else:
                    missing_data = True
                    #st.warning(f"Could not fetch DailyMed label data (Status: {label_response.status_code}).")
            else:
                missing_data = True
                #st.warning("Limited DailyMed data found.")
        else:
            missing_data = True
            #st.warning(f"Could not fetch DailyMed data (Status: {dailymed_response.status_code})")
    except Exception as e:
        missing_data = True
        #st.warning(f"Error fetching DailyMed data: {str(e)}.")

    # Fetch PubChem data for chemical formula
    try:
        chemical_data = get_pubchem_info(drug_name)
        if chemical_data:
            # Add chemical information to PubMed section
            data["pubmed"].append({
                "source": "PubChem",
                "pmid": "CHEM-1",
                "text": f"Chemical Formula: {chemical_data.get('formula', 'Not available')}. " +
                        f"Molecular Weight: {chemical_data.get('weight', 'Not available')}. " +
                        f"Structure Type: {chemical_data.get('structure_type', 'Not available')}.",
                "metadata": {"drug_name": drug_name.lower(), "publication_year": "Current"}
            })
            successful_sources.append("PubChem")
    except Exception as e:
        st.warning(f"Error fetching PubChem data: {str(e)}.")

    # ClinicalTrials.gov data with improved query and parsing
    # Update the ClinicalTrials.gov API request in your fetch_drug_data function
    try:
        # Create a fallback list of possible drug names for the search
        drug_names = [drug_name]

        # For known brand names, add generic names to improve search success
        brand_to_generic = {
            "keytruda": "pembrolizumab",
            "opdivo": "nivolumab",
            "humira": "adalimumab",
            "enbrel": "etanercept",
            "remicade": "infliximab",
            # Add more mappings as needed
        }

        # If we have a mapping for this drug, add the generic name as a fallback
        if drug_name.lower() in brand_to_generic:
            drug_names.append(brand_to_generic[drug_name.lower()])

        # Try each name until we get a success
        clinical_trials_found = False

        for name in drug_names:
            # Use the updated API format from ClinicalTrials.gov (as of 2023)
            ct_url = f"https://clinicaltrials.gov/api/v2/studies?query.term={name}&pageSize=10&format=json"
            ct_response = requests.get(ct_url)

            if ct_response.status_code == 200:
                ct_data = ct_response.json()

                # API v2 has a different structure
                if 'studies' in ct_data and len(ct_data['studies']) > 0:
                    for study in ct_data['studies']:
                        # Extract study information with the new structure
                        protocol = study.get('protocolSection', {})
                        identification = protocol.get('identificationModule', {})

                        trial_id = identification.get('nctId', 'Unknown')

                        # Phase extraction
                        design = protocol.get('designModule', {})
                        phase = design.get('phases', ['Unknown'])[0] if 'phases' in design and design[
                            'phases'] else 'Unknown'

                        # Description extraction
                        description = protocol.get('descriptionModule', {}).get('briefSummary',
                                                                                'No description available')

                        # Population extraction
                        eligibility = protocol.get('eligibilityModule', {})
                        criteria = eligibility.get('eligibilityCriteria', 'Study population not specified')
                        population = criteria.split('\n')[0] if '\n' in criteria else criteria[:100] + '...'

                        # Results and safety extraction simplified
                        results = "See ClinicalTrials.gov for complete results."
                        safety = "Safety data available on ClinicalTrials.gov"

                        # Add the trial to our data
                        data["clinical_trials"].append({
                            "source": "ClinicalTrials.gov",
                            "trial_id": trial_id,
                            "text": f"Study {trial_id}: A {phase} study of " +
                                    f"{name} in {population}... " +
                                    f"Description: {description[:150]}... " +
                                    f"Results: {results}",
                            "metadata": {"drug_name": name.lower(), "phase": phase if phase != 'Unknown' else ''}
                        })

                    clinical_trials_found = True
                    successful_sources.append("ClinicalTrials.gov")
                    break  # Exit the loop if we found trials

            # If this particular name didn't work, try the next one

        if not clinical_trials_found:
            missing_data = True
            #st.warning(f"Could not fetch clinical trials data for any of: {', '.join(drug_names)}")

    except Exception as e:
        missing_data = True
        #st.warning(f"Error fetching clinical trials data: {str(e)}.")

    # PubMed data
    try:
        # Use PubMed API to get publication data with more specific query
        pm_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={drug_name}+AND+(pharmacology[sb]+OR+mechanism+OR+clinical+trial[pt])&retmode=json&retmax=5"
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

                                # Try to identify mechanistic or pharmacological articles
                                is_mechanism = any(term in title.lower() or term in abstract.lower()
                                                   for term in ['mechanism', 'pharmacology', 'receptor', 'binding',
                                                                'agonist', 'antagonist', 'enzyme', 'molecular'])

                                data["pubmed"].append({
                                    "source": "PubMed",
                                    "pmid": pmid,
                                    "text": f"{title}. " +
                                            f"Abstract: {abstract[:300]}..." +
                                            (f" [MECHANISM/PHARMACOLOGY]" if is_mechanism else ""),
                                    "metadata": {"drug_name": drug_name.lower(), "publication_year": year,
                                                 "is_mechanism": is_mechanism}
                                })

                        if data["pubmed"]:
                            successful_sources.append("PubMed")
                        else:
                            missing_data = True
                            #st.warning("No PubMed article details found.")
                    else:
                        missing_data = True
                        st.warning(
                            f"Could not fetch PubMed article details (Status: {pm_details_response.status_code}).")
                else:
                    missing_data = True
                    st.warning("No PubMed articles found.")
            else:
                missing_data = True
                st.warning("Limited PubMed data found.")
        else:
            missing_data = True
            st.warning(f"Could not fetch PubMed data (Status: {pm_response.status_code}).")
    except Exception as e:
        missing_data = True
        st.warning(f"Error fetching PubMed data: {str(e)}.")

    # Always check if we're missing data or if key fields are empty
    missing_critical_data = (
            not data["fda_purple_book"] or
            not data["daily_med"] or
            len(data["clinical_trials"]) == 0 or
            len(data["pubmed"]) == 0 or
            "Indications not available" in data.get("daily_med", {}).get("text", "") or
            "Mechanism of action not available" in data.get("daily_med", {}).get("text", "")
    )

    if missing_data or missing_critical_data:
        # Display which data sources were successful and which need augmentation
        st.info(
            f"Successfully gathered data from: {', '.join(successful_sources) if successful_sources else 'No sources'}")
        missing_sources = []
        if not data["fda_purple_book"]:
            missing_sources.append("FDA approval information")
        if not data["daily_med"] or "Indications not available" in data.get("daily_med", {}).get("text", ""):
            missing_sources.append("Indications")
        if not data["daily_med"] or "Mechanism of action not available" in data.get("daily_med", {}).get("text", ""):
            missing_sources.append("Mechanism of action")
        if len(data["clinical_trials"]) == 0:
            missing_sources.append("Clinical trials")
        if len(data["pubmed"]) == 0:
            missing_sources.append("Literature data")

        if missing_sources:
            st.info(f"Using Sorcero AI to supplement missing data: {', '.join(missing_sources)}")

            # Use Claude to augment missing data
            try:
                augmented_data = augment_drug_data_with_claude(drug_name, data)

                # Merge the augmented data with our existing data
                data = merge_drug_data(data, augmented_data)
                st.success(f"Successfully augmented data with Sorcero AI.")
            except Exception as e:
                st.error(f"Error augmenting data with Sorcero AI: {str(e)}")
                traceback_str = traceback.format_exc()
                st.error(f"Traceback: {traceback_str}")

    return data


def fetch_openfda_data(drug_name):
    """Fetch comprehensive drug data from openFDA API."""

    # Dictionary to store all collected data
    fda_data = {
        "drug_info": {},
        "label_info": {},
        "adverse_events": []
    }

    try:
        # 1. Fetch drug product information
        drug_url = f"https://api.fda.gov/drug/drugsfda.json?search=openfda.generic_name:{drug_name}+OR+openfda.brand_name:{drug_name}&limit=3"
        drug_response = requests.get(drug_url)

        if drug_response.status_code == 200:
            drug_data = drug_response.json()
            if 'results' in drug_data and len(drug_data['results']) > 0:
                result = drug_data['results'][0]

                # Extract basic drug info
                fda_data["drug_info"] = {
                    "application_number": result.get('application_number', 'Unknown'),
                    "sponsor_name": result.get('sponsor_name', 'Unknown Manufacturer'),
                    "products": result.get('products', []),
                    "submissions": result.get('submissions', [])
                }

                # Get the most recent submission
                if result.get('submissions'):
                    sorted_submissions = sorted(
                        result['submissions'],
                        key=lambda x: x.get('submission_status_date', '0'),
                        reverse=True
                    )
                    fda_data["drug_info"]["latest_submission"] = sorted_submissions[0]

        # 2. Fetch detailed label information
        label_url = f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:{drug_name}+OR+openfda.generic_name:{drug_name}&limit=1"
        label_response = requests.get(label_url)

        if label_response.status_code == 200:
            label_data = label_response.json()
            if 'results' in label_data and len(label_data['results']) > 0:
                label = label_data['results'][0]

                # Extract key sections from the label
                fda_data["label_info"] = {
                    "indications_usage": label.get('indications_and_usage', ['Not available']),
                    "dosage_administration": label.get('dosage_and_administration', ['Not available']),
                    "contraindications": label.get('contraindications', ['Not available']),
                    "warnings": label.get('warnings', ['Not available']),
                    "adverse_reactions": label.get('adverse_reactions', ['Not available']),
                    "drug_interactions": label.get('drug_interactions', ['Not available']),
                    "mechanism_of_action": label.get('mechanism_of_action', ['Not available']),
                    "clinical_pharmacology": label.get('clinical_pharmacology', ['Not available']),
                    "clinical_studies": label.get('clinical_studies', ['Not available']),
                    "how_supplied": label.get('how_supplied', ['Not available'])
                }

        # 3. Fetch adverse events data (optional - can be large)
        events_url = f"https://api.fda.gov/drug/event.json?search=patient.drug.medicinalproduct:{drug_name}&limit=5"
        events_response = requests.get(events_url)

        if events_response.status_code == 200:
            events_data = events_response.json()
            if 'results' in events_data:
                fda_data["adverse_events"] = events_data['results']

        return fda_data

    except Exception as e:
        print(f"Error fetching openFDA data: {str(e)}")
        return fda_data


def get_pubchem_info(drug_name):
    """Fetch chemical information from PubChem API."""
    try:
        # First search for the compound
        search_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{drug_name}/cids/JSON"
        response = requests.get(search_url)

        if response.status_code == 200:
            data = response.json()
            if 'IdentifierList' in data and 'CID' in data['IdentifierList']:
                cid = data['IdentifierList']['CID'][0]

                # Get compound properties
                property_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/MolecularFormula,MolecularWeight,CanonicalSMILES,XLogP,Complexity/JSON"
                prop_response = requests.get(property_url)

                if prop_response.status_code == 200:
                    prop_data = prop_response.json()

                    if 'PropertyTable' in prop_data and 'Properties' in prop_data['PropertyTable'] and len(
                            prop_data['PropertyTable']['Properties']) > 0:
                        properties = prop_data['PropertyTable']['Properties'][0]

                        # Get classification information
                        structure_type = "Small Molecule"  # Default for most drugs
                        chemical_class = "Not specified"

                        # Determine chemical classification based on formula or SMILES
                        formula = properties.get('MolecularFormula', '')
                        smiles = properties.get('CanonicalSMILES', '')

                        # Determine structure type and class based on molecular features
                        if formula:
                            # Check if it's a peptide/protein (contains many C,N,O and has high weight)
                            if (formula.count('C') > 20 and formula.count('N') > 10 and
                                    formula.count('O') > 10 and int(properties.get('MolecularWeight', 0)) > 1000):
                                structure_type = "Peptide/Protein"
                                chemical_class = "Biologic"

                        if smiles:
                            # Check for common chemical classes based on SMILES patterns
                            if 'c1ccccc1' in smiles:  # Contains benzene ring
                                if 'N' in smiles and 'O' in smiles:
                                    chemical_class = "Benzene-derived Compound"
                            elif 'N1CCN' in smiles or 'n1ccn' in smiles:  # Contains piperazine
                                chemical_class = "Piperazine Derivative"
                            elif 'C(=O)N' in smiles:  # Contains amide
                                chemical_class = "Amide Derivative"
                            elif 'c1ccc2c(c1)' in smiles:  # Contains condensed rings
                                chemical_class = "Polycyclic Aromatic Compound"

                        return {
                            "formula": properties.get('MolecularFormula', 'Not available'),
                            "weight": properties.get('MolecularWeight', 'Not available'),
                            "smiles": properties.get('CanonicalSMILES', 'Not available'),
                            "logp": properties.get('XLogP', 'Not available'),
                            "complexity": properties.get('Complexity', 'Not available'),
                            "structure_type": structure_type,
                            "chemical_class": chemical_class,
                            "cid": cid
                        }

        return None
    except Exception as e:
        print(f"Error in PubChem API: {str(e)}")
        return None


def get_molecular_structure(drug_name):
    """Fetch and return molecular structure image URL for a drug."""
    try:
        # Step 1: Search for the compound to get the CID
        search_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{drug_name}/cids/JSON"
        response = requests.get(search_url)

        if response.status_code != 200:
            return None, "Could not find compound in PubChem"

        data = response.json()
        if 'IdentifierList' not in data or 'CID' not in data['IdentifierList']:
            return None, "No CID found for this compound"

        cid = data['IdentifierList']['CID'][0]

        # Step 2: Get the 2D structure image
        image_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG"

        # Step 3: Get compound properties
        property_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/MolecularFormula,MolecularWeight,CanonicalSMILES,XLogP,Complexity/JSON"
        prop_response = requests.get(property_url)

        if prop_response.status_code != 200:
            return image_url, "Structure available, but properties could not be retrieved"

        properties = prop_response.json()

        if 'PropertyTable' in properties and 'Properties' in properties['PropertyTable'] and len(
                properties['PropertyTable']['Properties']) > 0:
            prop_data = properties['PropertyTable']['Properties'][0]
            formula = prop_data.get('MolecularFormula', 'Not available')
            weight = prop_data.get('MolecularWeight', 'Not available')
            smiles = prop_data.get('CanonicalSMILES', 'Not available')
            logp = prop_data.get('XLogP', 'Not available')
            complexity = prop_data.get('Complexity', 'Not available')

            property_text = f"Formula: {formula}\nMolecular Weight: {weight} g/mol\nLogP: {logp}\nSMILES: {smiles}"
            return image_url, property_text

        return image_url, "Structure available, but no detailed properties found"

    except Exception as e:
        return None, f"Error retrieving chemical structure: {str(e)}"


def display_chemical_structure(drug_name):
    """Display the chemical structure in the Streamlit app."""
    image_url, properties = get_molecular_structure(drug_name)

    col1, col2 = st.columns([1, 1])

    with col1:
        if image_url:
            st.image(image_url, caption=f"Chemical structure of {drug_name}")
        else:
            st.warning("Chemical structure not available")

    with col2:
        st.subheader("Chemical Properties")
        st.text(properties)


def augment_drug_data_with_claude(drug_name, existing_data):
    """Use Claude API to fill in missing drug information with improved formatting and parsing."""

    try:
        # Get API key from Streamlit secrets
        if "ANTHROPIC_API_KEY" in st.secrets:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
        else:
            st.error("Anthropic API key not found in Streamlit secrets.")
            return existing_data  # Return existing data instead of empty dict

        # Extract what we already know to give context to Claude
        known_info = {
            "brand_name": existing_data.get("fda_purple_book", {}).get("metadata", {}).get("brand_name", ""),
            "manufacturer": "Unknown",
            "indications": "Not available",
            "mechanism": "Not available"
        }

        # Extract manufacturer from FDA data if available
        fda_text = existing_data.get("fda_purple_book", {}).get("text", "")
        if "Manufacturer:" in fda_text:
            known_info["manufacturer"] = fda_text.split("Manufacturer:")[1].split(".")[0].strip()

        # Extract indications from DailyMed data if available
        daily_med_text = existing_data.get("daily_med", {}).get("text", "")
        if "indicated for" in daily_med_text:
            known_info["indications"] = daily_med_text.split("indicated for")[1].split("Mechanism")[0].strip()

        # Extract mechanism from DailyMed data if available
        if "Mechanism of Action:" in daily_med_text:
            known_info["mechanism"] = daily_med_text.split("Mechanism of Action:")[1].strip()

        # Create a prompt that specifies what data we need and provides context
        prompt = f"""I need detailed, factual information about the pharmaceutical drug {drug_name} in JSON format.

Here's what I already know:
- Brand name: {known_info["brand_name"]}
- Manufacturer: {known_info["manufacturer"]}
- Indications: {known_info["indications"]}
- Mechanism of action: {known_info["mechanism"]}

Please provide the following information in valid JSON format only:

```json
{{
  "fda_data": {{
    "brand_name": "string",
    "approval_date": "string (format: YYYY-MM-DD)",
    "manufacturer": "string",
    "bla_nda_number": "string",
    "regulatory_status": "string"
  }},
  "daily_med_data": {{
    "indications": "string - detailed list of all approved indications",
    "mechanism_of_action": "string - detailed molecular explanation with receptor targets"
  }},
  "chemical_data": {{
    "formula": "string - chemical formula using standard notation",
    "structure_type": "string - chemical structure classification",
    "chemical_class": "string - broader chemical classification"
  }},
  "clinical_trials": [
    {{
      "trial_id": "string (NCT number if available)",
      "phase": "string (e.g., Phase 3)",
      "population": "string (patient population studied)",
      "results": "string (key efficacy findings with metrics)",
      "safety": "string (adverse events and percentages)"
    }}
  ]
}}
```

Please fill this structure with factual, specific and comprehensive information about {drug_name}. 
For chemical formula, use standard chemical notation.
For the mechanism of action, include molecular details about receptor binding, enzyme inhibition, or other relevant processes.
For clinical trials, focus on pivotal trials that led to approval when available.
If certain information is not available or cannot be determined, please indicate with "Not available" as the value.

Your response should ONLY include the JSON object with no additional text before or after.
"""

        # API endpoint
        url = "https://api.anthropic.com/v1/messages"

        # Headers
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        # Get the selected model from session state or use default
        selected_model = st.session_state.get('model_option', "claude-3-opus-20240229")

        # Request payload using the selected model
        data = {
            "model": selected_model,  # Use the model selected by the user
            "max_tokens": 4000,
            "temperature": 0,
            "system": "You are a pharmaceutical information specialist with extensive knowledge of drugs, their approvals, mechanisms, clinical trials, and research literature. Provide only factual, accurate information. Be precise, detailed and comprehensive. Return your response in valid JSON format only, with no additional text.",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        # Make the request
        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code != 200:
            st.error(f"Error from Claude API: Status {response.status_code}")
            st.error(f"Response: {response.text}")
            return existing_data  # Return existing data instead of empty dict

        # Parse the response
        result = response.json()
        content = result.get("content", [{}])[0].get("text", "")

        #st.success("Successfully received information from Claude!")

        # Try to parse the JSON response
        # Look for JSON within code blocks first
        json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', content)
        if json_match:
            json_str = json_match.group(1)
            try:
                claude_data = json.loads(json_str)

                # Transform the Claude JSON response into our expected format
                augmented_data = transform_claude_json_to_app_format(drug_name, claude_data)

                # Merge the augmented data with existing data
                return merge_drug_data(existing_data, augmented_data)
            except json.JSONDecodeError:
                st.error("Failed to parse JSON from Sorcero AI")
                return existing_data
        else:
            # Try to find JSON object without code blocks
            json_match = re.search(r'({[\s\S]*})', content)
            if json_match:
                json_str = json_match.group(1)
                try:
                    claude_data = json.loads(json_str)

                    # Transform the Claude JSON response into our expected format
                    augmented_data = transform_claude_json_to_app_format(drug_name, claude_data)

                    # Merge the augmented data with existing data
                    return merge_drug_data(existing_data, augmented_data)
                except json.JSONDecodeError:
                    st.error("Failed to parse JSON from Sorcero AI")
                    return existing_data
            else:
                # Fall back to the original parsing method
                st.warning("Could not find JSON in Sorcero AI. Falling back to text extraction.")
                return parse_claude_text_response(drug_name, content, existing_data)

    except Exception as e:
        st.error(f"Error in Sorcero AI function: {str(e)}")
        traceback_str = traceback.format_exc()
        st.error(f"Traceback: {traceback_str}")
        return existing_data  # Return existing data instead of empty dict


def transform_claude_json_to_app_format(drug_name, claude_data):
    """Transform the JSON response from Claude into the format expected by the app."""

    # Initialize the data structure
    app_data = {
        "fda_purple_book": {},
        "daily_med": {},
        "clinical_trials": [],
        "pubmed": []
    }

    # Extract FDA Purple Book data
    if "fda_data" in claude_data:
        fda = claude_data["fda_data"]
        brand_name = fda.get("brand_name", drug_name.upper())
        approval_date = fda.get("approval_date", "Unknown")
        manufacturer = fda.get("manufacturer", "Unknown")
        bla_nda = fda.get("bla_nda_number", "Unknown")
        status = fda.get("regulatory_status", "Unknown")

        app_data["fda_purple_book"] = {
            "source": "FDA Purple Book",
            "text": f"{brand_name} ({drug_name}) - New Molecular Entity. Approved by FDA on {approval_date}. " +
                    f"Manufacturer: {manufacturer}. " +
                    f"BLA/NDA Number: {bla_nda}. " +
                    f"Current Regulatory Status: {status}.",
            "metadata": {"drug_name": drug_name.lower(), "brand_name": brand_name}
        }

    # Extract DailyMed data
    if "daily_med_data" in claude_data:
        dm = claude_data["daily_med_data"]
        indications = dm.get("indications", "Indications not available.")
        mechanism = dm.get("mechanism_of_action", "Mechanism of action not available.")

        # Get brand name from FDA data or default to uppercase drug name
        brand_name = claude_data.get("fda_data", {}).get("brand_name", drug_name.upper())

        app_data["daily_med"] = {
            "source": "DailyMed",
            "text": f"{brand_name} ({drug_name.lower()}) is a pharmaceutical agent indicated for: " +
                    indications + " " +
                    "Mechanism of Action: " + mechanism,
            "metadata": {"drug_name": drug_name.lower(), "document_type": "label"}
        }

    # Extract Clinical Trials data
    if "clinical_trials" in claude_data:
        for i, trial in enumerate(claude_data["clinical_trials"]):
            trial_id = trial.get("trial_id", f"Trial-{i + 1}")
            phase = trial.get("phase", "Unknown")
            population = trial.get("population", "Not specified")
            results = trial.get("results", "Results not reported")
            safety = trial.get("safety", "Safety data not reported")

            app_data["clinical_trials"].append({
                "source": "ClinicalTrials.gov",
                "trial_id": trial_id,
                "text": f"Study {trial_id}: A {phase} study of {drug_name} in {population}. " +
                        f"Results: {results[:200]}... " +
                        f"Safety: {safety[:150]}...",
                "metadata": {"drug_name": drug_name.lower(), "phase": phase}
            })

    # Extract chemical data and add to PubMed as that's where we typically store this in the app
    if "chemical_data" in claude_data:
        chem = claude_data["chemical_data"]
        formula = chem.get("formula", "Not available")
        structure = chem.get("structure_type", "Not specified")
        chem_class = chem.get("chemical_class", "Not specified")

        app_data["pubmed"].append({
            "source": "PubMed",
            "pmid": "CHEM-1",
            "text": f"Chemical Formula: {formula}. Structure Type: {structure}. Chemical Class: {chem_class}.",
            "metadata": {"drug_name": drug_name.lower(), "publication_year": "Current"}
        })

    return app_data


def merge_drug_data(existing_data, new_data):
    """Merge existing data with new data, preferring existing data when available."""

    # Deep copy existing data to avoid modifying the original
    merged_data = copy.deepcopy(existing_data)

    # For each data category
    for key in new_data:
        # If the category is empty in existing data, use the new data
        if not merged_data.get(key):
            merged_data[key] = new_data[key]
        # For list types (clinical_trials, pubmed)
        elif isinstance(merged_data[key], list):
            if len(merged_data[key]) == 0:
                merged_data[key] = new_data[key]
        # For dict types with specific missing data
        elif isinstance(merged_data[key], dict):
            # For daily_med, check if specific key phrases are missing
            if key == "daily_med":
                if "Indications not available" in merged_data[key].get("text", "") and "indicated for" in new_data[
                    key].get("text", ""):
                    merged_data[key] = new_data[key]
                elif "Mechanism of action not available" in merged_data[key].get("text",
                                                                                 "") and "Mechanism of Action:" in \
                        new_data[key].get("text", ""):
                    # Just update the mechanism part
                    original_text = merged_data[key].get("text", "")
                    if "Mechanism of Action:" in original_text:
                        # Replace just the mechanism part
                        before_mech = original_text.split("Mechanism of Action:")[0]
                        new_mech = new_data[key].get("text", "").split("Mechanism of Action:")[1]
                        merged_data[key]["text"] = before_mech + "Mechanism of Action:" + new_mech
                    else:
                        # Append the mechanism
                        merged_data[key]["text"] = original_text + " Mechanism of Action:" + \
                                                   new_data[key].get("text", "").split("Mechanism of Action:")[1]

    return merged_data


def parse_claude_text_response(drug_name, content, existing_data):
    """Fall back to text parsing if JSON parsing fails."""
    # This function maintains the original regex-based parsing as a fallback

    # Initialize the data structure
    augmented_data = {
        "fda_purple_book": {},
        "daily_med": {},
        "clinical_trials": [],
        "pubmed": []
    }

    # Extract FDA Purple Book data
    fda_match = re.search(r'FDA (?:Purple Book|data|information):(.*?)(?=\d+\.\s+Daily Med|$)', content,
                          re.DOTALL | re.IGNORECASE)
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
    if daily_med_match and (
            not existing_data.get("daily_med") or "Indications not available" in existing_data.get("daily_med",
                                                                                                   {}).get("text",
                                                                                                           "")):
        daily_med_text = daily_med_match.group(1).strip()
        # Extract indications
        indications_match = re.search(
            r'(?:Detailed )?[Ii]ndications and usage[:\s-]+(.+?)(?=(?:Complete )?[Mm]echanism of action|$)',
            daily_med_text, re.DOTALL | re.IGNORECASE)
        indications = indications_match.group(1).strip() if indications_match else "Indications not available."
        # Extract mechanism
        mechanism_match = re.search(r'(?:Complete )?[Mm]echanism of action[:\s-]+(.+?)(?=\n\d+\.|$)',
                                    daily_med_text, re.DOTALL | re.IGNORECASE)
        mechanism = mechanism_match.group(1).strip() if mechanism_match else "Mechanism of action not available."

        # Get brand name from FDA data or default to uppercase drug name
        brand_name = existing_data.get("fda_purple_book", {}).get("metadata", {}).get("brand_name",
                                                                                      drug_name.upper())
        if not brand_name and augmented_data.get("fda_purple_book"):
            brand_name = augmented_data.get("fda_purple_book", {}).get("metadata", {}).get("brand_name",
                                                                                           drug_name.upper())

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

        # Look for trials by several patterns
        trial_blocks = []

        # Try to split by trial numbers/IDs first
        pattern1 = re.compile(r'(?:Trial|Study)\s*\d+:|NCT\d+:|(?:^|\n)\s*-\s*Trial ID', re.IGNORECASE)
        matches1 = list(pattern1.finditer(ct_text))

        if matches1:
            # For each match, extract the text up to the next match or the end
            for i in range(len(matches1)):
                start = matches1[i].start()
                end = matches1[i + 1].start() if i < len(matches1) - 1 else len(ct_text)
                trial_blocks.append(ct_text[start:end])
        else:
            # Try alternate pattern - looking for dashed or bulleted lists
            pattern2 = re.compile(r'(?:^|\n)\s*[-•*]\s+', re.IGNORECASE)
            matches2 = list(pattern2.finditer(ct_text))

            if matches2:
                for i in range(len(matches2)):
                    start = matches2[i].start()
                    end = matches2[i + 1].start() if i < len(matches2) - 1 else len(ct_text)
                    trial_blocks.append(ct_text[start:end])
            else:
                # If no clear structure, try to split by double newlines
                trial_blocks = ct_text.split("\n\n")

        # Process each trial block
        for i, block in enumerate(trial_blocks, 1):
            if len(block.strip()) < 10:  # Skip very short blocks
                continue

            # Extract trial ID
            trial_id_match = re.search(r'(?:Trial|Study)?\s*ID:?\s*(NCT\d+|[A-Z0-9\-.]+)', block, re.IGNORECASE)
            if not trial_id_match:
                trial_id_match = re.search(r'(NCT\d+)', block, re.IGNORECASE)
            trial_id = trial_id_match.group(1).strip() if trial_id_match else f"Trial-{i}"

            # Extract phase
            phase_match = re.search(r'Phase:?\s*([0-9/IV]+)', block, re.IGNORECASE)
            if not phase_match:
                phase_match = re.search(r'Phase\s+([0-9/IV]+)', block, re.IGNORECASE)
            phase = phase_match.group(1).strip() if phase_match else "Unknown"

            # Clean up phase
            if phase == "3" or phase == "III":
                phase = "Phase 3"
            elif phase == "2" or phase == "II":
                phase = "Phase 2"
            elif phase == "1" or phase == "I":
                phase = "Phase 1"
            elif phase == "4" or phase == "IV":
                phase = "Phase 4"
            elif "/" in phase:
                phase = f"Phase {phase}"
            else:
                phase = f"Phase {phase}"

            # Extract population
            population_match = re.search(r'(?:Study )?[Pp]opulation:?\s+(.+?)(?=\n|$)', block, re.IGNORECASE)
            if not population_match:
                population_match = re.search(
                    r'in (?:patients with|subjects with|participants with|adults with) (.+?)(?=[\.,:;]|$)', block,
                    re.IGNORECASE)
            population = population_match.group(1).strip() if population_match else "Not specified"

            # Extract results
            results_match = re.search(r'(?:Key )?[Rr]esults:?\s+(.+?)(?=(?:Safety|Adverse|$))', block,
                                      re.DOTALL | re.IGNORECASE)
            results = results_match.group(1).strip() if results_match else "Results not reported"

            # Extract safety
            safety_match = re.search(
                r'(?:Safety|Adverse)(?:\s+(?:information|events|effects|reactions))?:?\s+(.+?)(?=\n\n|$)', block,
                re.DOTALL | re.IGNORECASE)
            safety = safety_match.group(1).strip() if safety_match else "Safety data not reported"

            # Create trial entry
            augmented_data["clinical_trials"].append({
                "source": "ClinicalTrials.gov",
                "trial_id": trial_id,
                "text": f"Study {trial_id}: A {phase} study of {drug_name} in {population}. " +
                        f"Results: {results[:200]}... " +
                        f"Safety: {safety[:150]}...",
                "metadata": {"drug_name": drug_name.lower(), "phase": phase}
            })

    # Extract chemical data
    chem_match = re.search(r'Chemical (?:data|information|properties).*?:(.*?)(?=\n\n|$)', content,
                           re.DOTALL | re.IGNORECASE)
    if chem_match:
        chem_text = chem_match.group(1).strip()

        # Extract formula
        formula_match = re.search(r'(?:Chemical )?[Ff]ormula:?\s+([A-Za-z0-9]+)', chem_text)
        formula = formula_match.group(1) if formula_match else "Not available"

        # Extract structure type
        structure_match = re.search(r'[Ss]tructure [Tt]ype:?\s+(.+?)(?=\n|$)', chem_text)
        structure = structure_match.group(1).strip() if structure_match else "Not specified"

        # Extract chemical class
        class_match = re.search(r'[Cc]hemical [Cc]lass:?\s+(.+?)(?=\n|$)', chem_text)
        chem_class = class_match.group(1).strip() if class_match else "Not specified"

        # Add to pubmed data
        augmented_data["pubmed"].append({
            "source": "Chemical Data",
            "pmid": "CHEM-1",
            "text": f"Chemical Formula: {formula}. Structure Type: {structure}. Chemical Class: {chem_class}.",
            "metadata": {"drug_name": drug_name.lower(), "publication_year": "Current"}
        })

    return merge_drug_data(existing_data, augmented_data)


# Define the main app
def main():
    """Main function for the PharmD Agent Explorer app with enhanced features."""

    # Set page configuration
    set_page_config()

    # Add sidebar and styling
    add_sidebar_and_styling()

    # Check if the API key is set
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
            if not api_key or api_key == "your_anthropic_api_key_here":
                st.error(
                    "⚠️ Anthropic API key is not set or is using the default value. Please set your API key in .streamlit/secrets.toml")
                st.info(
                    "Without an API key, the app will attempt to use only public APIs, but results may be incomplete.")
        else:
            st.error("⚠️ Anthropic API key not found in secrets. Please set your API key in .streamlit/secrets.toml")
            st.info("Without an API key, the app will attempt to use only public APIs, but results may be incomplete.")
    except Exception as e:
        st.error(f"⚠️ Error accessing Streamlit secrets: {e}")
        st.info("Without an API key, the app will attempt to use only public APIs, but results may be incomplete.")

    # Add a sidebar option to clear results
    if st.session_state.get('results_displayed', False):
        if st.sidebar.button("Clear Results & Start New Search"):
            st.session_state.results_displayed = False
            st.session_state.drug_data = None
            st.session_state.profile = None
            st.session_state.visualization = None
            st.rerun()

    # Main content area
    st.title("PharmD Agent Explorer")
    st.subheader(
        "Generate profiles for pharmaceutical assets using Sorcero AI and built-in domain data in the Sorcero Scientific Data Pool")

    # If results are not displayed, show the input form
    if not st.session_state.get('results_displayed', False):
        # Create a form for input
        with st.form("drug_input_form"):
            st.markdown("### Generate Asset Profile")
            st.markdown("Enter the name of a pharmaceutical asset to generate a detailed markdown profile")

            # Input for drug name
            drug_name = st.text_input("", placeholder="Enter Asset name")

            # Optional settings accordion
            with st.expander("Advanced Options"):
                model_option = st.selectbox(
                    "Sorcero AI Agents for Data Augmentation",
                    ["claude-3-opus-20240229", "claude-3-haiku-20240307", "claude-3-5-sonnet-20240620"],
                    index=0,
                    help="Select which Agent to use for data augmentation."
                )

                include_chemical_structure = st.checkbox(
                    "Include Chemical Structure Visualization",
                    value=True,
                    help="Display molecular structure and chemical properties of the drug"
                )

                data_sources = st.multiselect(
                    "Data Sources to Query",
                    ["FDA", "DailyMed", "ClinicalTrials.gov", "PubMed", "PubChem", "Sorcero AI"],
                    default=["FDA", "DailyMed", "ClinicalTrials.gov", "PubMed", "PubChem", "Sorcero AI"],
                    help="Select which data sources to query for information"
                )

            # Submit button
            submit_button = st.form_submit_button("Generate Profile")

            if submit_button and drug_name:
                # Store advanced options in session state
                st.session_state.model_option = model_option
                st.session_state.include_chemical_structure = include_chemical_structure
                st.session_state.data_sources = data_sources

                with st.spinner(f"Generating profile for {drug_name}..."):
                    try:
                        # Create a status container for progress updates
                        status_container = st.empty()
                        status_container.info(f"Searching for information about {drug_name}...")

                        # Fetch data for the specified drug
                        drug_data = fetch_drug_data(drug_name)
                        st.session_state.drug_data = drug_data

                        # Store chemical structure information if enabled
                        if st.session_state.include_chemical_structure:
                            status_container.info("Fetching molecular structure from PubChem...")
                            image_url, properties = get_molecular_structure(drug_name)
                            st.session_state.chemical_structure = {
                                "image_url": image_url,
                                "properties": properties
                            }

                        status_container.info("Generating asset profile...")

                        # Initialize the drug profile generator
                        profile_generator = DrugAssetProfileGenerator()

                        # Generate the profile
                        profile = profile_generator.generate_asset_profile(drug_name, drug_data)
                        st.session_state.profile = profile

                        # Generate visualization
                        visualization = profile_generator.visualize_drug_ontology(drug_name,
                                                                                  profile.get("Drug Ontology", {}))
                        st.session_state.visualization = visualization

                        # Generate enhanced markdown
                        if st.session_state.include_chemical_structure:
                            markdown_output = generate_enhanced_asset_markdown(
                                profile,
                                visualization,
                                st.session_state.get('chemical_structure')
                            )
                        else:
                            markdown_output = generate_asset_markdown(profile, visualization)

                        st.session_state.markdown_output = markdown_output

                        # Set flag to display results
                        st.session_state.results_displayed = True

                        # Clear status
                        status_container.empty()

                        # Rerun to refresh the UI
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating profile: {str(e)}")
                        traceback_str = traceback.format_exc()
                        st.error(f"Traceback: {traceback_str}")

    # If results are available, display them
    else:
        if st.session_state.get('markdown_output'):
            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["Drug Profile", "Chemical Structure", "Raw Data"])

            with tab1:
                # Display the markdown profile
                st.markdown(st.session_state.markdown_output, unsafe_allow_html=True)

            with tab2:
                # Display chemical structure if available
                if st.session_state.get('include_chemical_structure', True) and st.session_state.get(
                        'chemical_structure'):
                    chemical_data = st.session_state.chemical_structure

                    col1, col2 = st.columns([1, 1])

                    with col1:
                        if chemical_data.get('image_url'):
                            st.image(chemical_data['image_url'],
                                     caption=f"Chemical structure of {st.session_state.profile['Asset Profile']}")
                        else:
                            st.warning("Chemical structure image not available")

                    with col2:
                        st.subheader("Chemical Properties")
                        st.text(chemical_data.get('properties', 'No property data available'))

                        # Add 3D structure viewer button if structure is available
                        if chemical_data.get('image_url'):
                            drug_name = st.session_state.profile['Asset Profile']
                            st.markdown(
                                f"[View 3D Structure on PubChem](https://pubchem.ncbi.nlm.nih.gov/#query={drug_name})")
                else:
                    st.info(
                        "Chemical structure visualization was not enabled for this drug. Generate a new profile with Chemical Structure Visualization enabled to see this data.")

            with tab3:
                # Display raw data sources
                st.subheader("Raw Data Sources")

                # Create expandable sections for each data source
                if st.session_state.get('drug_data'):
                    drug_data = st.session_state.drug_data

                    # FDA Purple Book
                    with st.expander("FDA Purple Book Data"):
                        if drug_data.get('fda_purple_book'):
                            st.markdown(f"**Source**: {drug_data['fda_purple_book'].get('source', 'FDA Purple Book')}")
                            st.markdown(f"**Text**: {drug_data['fda_purple_book'].get('text', 'No data available')}")
                        else:
                            st.warning("No FDA Purple Book data available")

                    # DailyMed
                    with st.expander("DailyMed Data"):
                        if drug_data.get('daily_med'):
                            st.markdown(f"**Source**: {drug_data['daily_med'].get('source', 'DailyMed')}")
                            st.markdown(f"**Text**: {drug_data['daily_med'].get('text', 'No data available')}")
                        else:
                            st.warning("No DailyMed data available")

                    # Clinical Trials
                    with st.expander("Clinical Trials Data"):
                        if drug_data.get('clinical_trials') and len(drug_data['clinical_trials']) > 0:
                            for i, trial in enumerate(drug_data['clinical_trials']):
                                st.markdown(f"**Trial {i + 1}**: {trial.get('trial_id', 'Unknown ID')}")
                                st.markdown(f"**Source**: {trial.get('source', 'ClinicalTrials.gov')}")
                                st.markdown(f"**Text**: {trial.get('text', 'No data available')}")
                                st.markdown("---")
                        else:
                            st.warning("No Clinical Trials data available")

                    # PubMed
                    with st.expander("PubMed/Literature Data"):
                        if drug_data.get('pubmed') and len(drug_data['pubmed']) > 0:
                            for i, article in enumerate(drug_data['pubmed']):
                                st.markdown(f"**Article {i + 1}**: {article.get('pmid', 'Unknown PMID')}")
                                st.markdown(f"**Source**: {article.get('source', 'PubMed')}")
                                st.markdown(f"**Text**: {article.get('text', 'No data available')}")
                                st.markdown("---")
                        else:
                            st.warning("No PubMed data available")
                else:
                    st.warning("No raw data available")

            # Add a button at the bottom to start a new search
            if st.button("Generate Another Profile"):
                st.session_state.results_displayed = False
                st.session_state.drug_data = None
                st.session_state.profile = None
                st.session_state.visualization = None
                st.session_state.chemical_structure = None
                st.rerun()
        else:
            st.error("No markdown output found in session state")
            if st.button("Start Over"):
                st.session_state.results_displayed = False
                st.rerun()

# Initialize session state if needed
if 'results_displayed' not in st.session_state:
    st.session_state.results_displayed = False

# Run the app
if __name__ == "__main__":
    main()
