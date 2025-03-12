# pharmD_agent_explorer

# PharmD Agent Explorer

Generate comprehensive markdown profiles for pharmaceutical assets using AI.

## Overview

PharmD Agent Explorer is a Streamlit application that generates detailed drug profiles by querying real pharmaceutical data sources and augmenting that information with Claude AI. The app integrates data from FDA, DailyMed, ClinicalTrials.gov, and PubMed to create comprehensive, structured profiles of pharmaceutical drugs.

## Features

- **Real-time Data Retrieval**: Fetches up-to-date information from authoritative pharmaceutical sources
- **AI-Powered Augmentation**: Uses Claude to fill in gaps when data sources are incomplete
- **Comprehensive Drug Profiles**: Includes:
  - Identifiers (brand name, generic name, approval date, etc.)
  - Approval status
  - Indications and usage
  - Mechanism of action
  - Clinical evidence summaries
  - Drug ontology and classification
  - Semantic relationships

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- An Anthropic API key (for Claude)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/pharmd-agent-explorer.git
   cd pharmd-agent-explorer
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.streamlit` directory and add your API key:
   ```
   mkdir -p .streamlit
   cp .streamlit-secrets-template.toml .streamlit/secrets.toml
   ```
   
4. Edit `.streamlit/secrets.toml` and replace `your_anthropic_api_key_here` with your actual Anthropic API key.

### Running the Application

Start the Streamlit app:
```
streamlit run app.py
```

The application will be accessible at http://localhost:8501 in your web browser.

## Deploying to Streamlit Cloud

1. Push your code to GitHub (make sure to exclude `.streamlit/secrets.toml` from your repository).

2. Connect your GitHub repository to [Streamlit Cloud](https://streamlit.io/cloud).

3. Add your Anthropic API key in the Streamlit Cloud secrets management section.

4. Deploy your app.

## Project Structure

- `app.py`: Main Streamlit application
- `drug_ontology.py`: Contains the DrugOntologyBuilder and DrugAssetProfileGenerator classes
- `requirements.txt`: Required Python packages
- `.streamlit/secrets.toml`: Configuration for API keys (not included in repository)

## Acknowledgments

- FDA Purple Book
- DailyMed
- ClinicalTrials.gov
- PubMed
- Anthropic Claude AI
