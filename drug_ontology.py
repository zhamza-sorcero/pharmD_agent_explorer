import pandas as pd
import json
import re


class DrugOntologyBuilder:
    """Builds drug ontologies and taxonomies."""

    def build_ontology(self, drug_data):
        """Build a comprehensive ontology structure for a drug based on its profile data."""
        drug_name = drug_data.get("asset_name", "")
        brand_name = drug_data.get("identifiers", {}).get("brand_name", "")

        # Build classification hierarchy
        classifications = self._build_classification_hierarchy(drug_data)

        # Build ontological relationships
        relationships = self._build_ontological_relationships(drug_data)

        # Build semantic network
        semantic_network = self._build_semantic_network(drug_data)

        return {
            "drug_name": drug_name,
            "brand_name": brand_name,
            "classifications": classifications,
            "relationships": relationships,
            "semantic_network": semantic_network
        }

    def _build_classification_hierarchy(self, drug_data):
        """Build the classification hierarchy for the drug."""
        # Extract drug class information
        drug_class = drug_data.get("approval_status", {}).get("drug_class", "")
        mechanism = drug_data.get("mechanism_of_action", "")
        indications = drug_data.get("indications", [])

        # Determine pharmaceutical classification
        pharm_class = {
            "class": "Central Nervous System Agents",
            "subclass": "Psychotropic Agents",
            "family": "Antipsychotics" if "antipsychotic" in drug_class.lower() else "Psychotherapeutic Agents",
            "subfamily": "Atypical (Second-Generation) Antipsychotics" if "atypical" in drug_class.lower() else "",
            "type": self._extract_drug_type(mechanism),
            "agent": drug_data.get("asset_name", "")
        }

        # Determine pharmacological classification
        targets = self._extract_targets(mechanism)

        # Determine therapeutic classification
        therapeutic_areas = self._extract_therapeutic_areas(indications)

        # Determine chemical classification
        chemical_class = self._extract_chemical_class(drug_data)

        return {
            "pharmaceutical": pharm_class,
            "pharmacological": {
                "primary_mechanism": "Receptor Modulator",
                "targets": targets
            },
            "therapeutic": therapeutic_areas,
            "chemical": chemical_class
        }

    def _extract_drug_type(self, mechanism):
        """Extract drug type based on mechanism description."""
        if "serotonin-dopamine" in mechanism.lower():
            return "Serotonin-Dopamine Activity Modulators (SDAMs)"
        elif "partial agonist" in mechanism.lower() and "antagonist" in mechanism.lower():
            return "Partial Agonist-Antagonist"
        elif "serotonin" in mechanism.lower() or "5-ht" in mechanism.lower():
            return "Serotonergic Agent"
        elif "dopamine" in mechanism.lower() or "d2" in mechanism.lower():
            return "Dopaminergic Agent"
        elif "cholinergic" in mechanism.lower() or "acetylcholine" in mechanism.lower():
            return "Cholinergic Agent"
        elif "gaba" in mechanism.lower():
            return "GABAergic Agent"
        elif "histamine" in mechanism.lower() or "h1" in mechanism.lower():
            return "Histaminergic Agent"
        elif "adrenergic" in mechanism.lower() or "norepinephrine" in mechanism.lower():
            return "Adrenergic Agent"
        elif "inhibit" in mechanism.lower() and "reuptake" in mechanism.lower():
            return "Reuptake Inhibitor"
        else:
            return "Novel Agent"

    def _extract_targets(self, mechanism):
        """Extract receptor targets from mechanism description."""
        targets = []

        # Check for common CNS drug targets
        receptor_keywords = [
            ("D2", "dopamine", "dopaminergic"),
            ("5-HT1A", "serotonin", "serotonergic"),
            ("5-HT2A", "serotonin", "serotonergic"),
            ("α1", "adrenergic", "noradrenergic"),
            ("α2", "adrenergic", "noradrenergic"),
            ("H1", "histamine", "histaminergic"),
            ("M1", "muscarinic", "cholinergic"),
            ("GABA", "GABA", "GABAergic"),
            ("NMDA", "glutamate", "glutamatergic"),
            ("NK1", "neurokinin", "neurokininergic"),
            ("μ-opioid", "opioid", "opioidergic"),
            ("κ-opioid", "opioid", "opioidergic"),
            ("δ-opioid", "opioid", "opioidergic")
        ]

        activity_types = ["agonist", "antagonist", "partial agonist", "inverse agonist", "modulator", "inhibitor"]

        for receptor_terms in receptor_keywords:
            for term in receptor_terms:
                if term.lower() in mechanism.lower():
                    # Find the activity type
                    activity = "unknown"
                    for act_type in activity_types:
                        if act_type.lower() in mechanism.lower():
                            activity = act_type
                            break

                    # Add the target
                    targets.append({
                        "receptor": receptor_terms[0],
                        "family": receptor_terms[1].capitalize() + " Receptors",
                        "activity": activity.capitalize()
                    })
                    break

        # If no specific targets found, try to infer from common terms
        if not targets:
            if "reuptake inhibitor" in mechanism.lower():
                if "serotonin" in mechanism.lower() or "5-ht" in mechanism.lower():
                    targets.append({
                        "receptor": "SERT",
                        "family": "Serotonin Transporters",
                        "activity": "Inhibitor"
                    })
                if "dopamine" in mechanism.lower():
                    targets.append({
                        "receptor": "DAT",
                        "family": "Dopamine Transporters",
                        "activity": "Inhibitor"
                    })
                if "norepinephrine" in mechanism.lower() or "noradrenaline" in mechanism.lower():
                    targets.append({
                        "receptor": "NET",
                        "family": "Norepinephrine Transporters",
                        "activity": "Inhibitor"
                    })

        return targets

    def _extract_therapeutic_areas(self, indications):
        """Extract therapeutic areas from indications."""
        psychiatric = []
        neurological = []
        cardiovascular = []
        respiratory = []
        infectious = []
        metabolic = []
        oncology = []
        immune = []
        other = []

        # Common condition keywords by therapeutic area
        condition_categories = {
            "psychiatric": ["depression", "schizophrenia", "bipolar", "anxiety", "ocd", "adhd", "insomnia",
                            "psychiatric", "mental", "psychosis", "psychotic", "mood"],
            "neurological": ["alzheimer", "parkinson", "huntington", "dementia", "epilepsy", "seizure",
                             "multiple sclerosis", "migraine", "headache", "stroke", "cerebral", "brain", "neural",
                             "neuron", "neuropathic", "neurological"],
            "cardiovascular": ["heart", "cardiac", "cardio", "hypertension", "blood pressure", "arrhythmia", "stroke",
                               "cholesterol", "lipid", "angina", "myocardial", "thrombosis", "embolism", "vascular"],
            "respiratory": ["asthma", "copd", "bronchitis", "pneumonia", "respiratory", "pulmonary", "lung", "breath",
                            "breathing", "airway", "bronchial"],
            "infectious": ["infection", "bacterial", "viral", "fungal", "pathogen", "antibiotic", "antimicrobial",
                           "antiviral", "antifungal", "hiv", "aids", "herpes", "hepatitis"],
            "metabolic": ["diabetes", "thyroid", "metabolism", "metabolic", "obesity", "weight", "glycemic",
                          "hyperglycemia", "hyperlipidemia", "insulin", "gout"],
            "oncology": ["cancer", "tumor", "carcinoma", "sarcoma", "lymphoma", "leukemia", "melanoma", "oncology",
                         "malignant", "neoplasm"],
            "immune": ["immune", "autoimmune", "allergy", "allergic", "arthritis", "rheumatoid", "psoriasis",
                       "inflammation", "inflammatory", "transplant"]
        }

        for indication in indications:
            indication_lower = indication.lower()

            # Check which category the indication belongs to
            matched = False
            for category, keywords in condition_categories.items():
                if any(keyword in indication_lower for keyword in keywords):
                    if category == "psychiatric":
                        psychiatric.append(indication)
                    elif category == "neurological":
                        neurological.append(indication)
                    elif category == "cardiovascular":
                        cardiovascular.append(indication)
                    elif category == "respiratory":
                        respiratory.append(indication)
                    elif category == "infectious":
                        infectious.append(indication)
                    elif category == "metabolic":
                        metabolic.append(indication)
                    elif category == "oncology":
                        oncology.append(indication)
                    elif category == "immune":
                        immune.append(indication)
                    matched = True
                    break

            # If not matched to any category, add to other
            if not matched:
                other.append(indication)

        result = {}
        if psychiatric:
            result["Psychiatric Disorders"] = psychiatric
        if neurological:
            result["Neurological Disorders"] = neurological
        if cardiovascular:
            result["Cardiovascular Disorders"] = cardiovascular
        if respiratory:
            result["Respiratory Disorders"] = respiratory
        if infectious:
            result["Infectious Diseases"] = infectious
        if metabolic:
            result["Metabolic Disorders"] = metabolic
        if oncology:
            result["Oncology"] = oncology
        if immune:
            result["Immune Disorders"] = immune
        if other:
            result["Other Conditions"] = other

        return result

    def _extract_chemical_class(self, drug_data):
        """Extract chemical classification data."""
        # Get the drug name and mechanism
        drug_name = drug_data.get("asset_name", "").lower()
        mechanism = drug_data.get("mechanism_of_action", "").lower()

        # Dictionary of common drug chemical classes and their related compounds
        chemical_classes = {
            # Antipsychotics
            "phenothiazine": {
                "structure_type": "Phenothiazine",
                "chemical_class": "Tricyclic Compounds",
                "related": ["chlorpromazine", "fluphenazine", "prochlorperazine"]
            },
            "butyrophenone": {
                "structure_type": "Butyrophenone",
                "chemical_class": "Halogenated Compounds",
                "related": ["haloperidol", "droperidol"]
            },
            "thioxanthene": {
                "structure_type": "Thioxanthene",
                "chemical_class": "Tricyclic Compounds",
                "related": ["thiothixene", "flupenthixol"]
            },
            "benzisoxazole": {
                "structure_type": "Benzisoxazole",
                "chemical_class": "Heterocyclic Compounds",
                "related": ["risperidone", "paliperidone", "iloperidone"]
            },
            "quinolone": {
                "structure_type": "Quinolinone Derivative",
                "chemical_class": "Heterocyclic Compounds",
                "related": ["aripiprazole", "brexpiprazole", "cariprazine"]
            },

            # Antidepressants
            "ssri": {
                "structure_type": "Various",
                "chemical_class": "Selective Serotonin Reuptake Inhibitors",
                "related": ["fluoxetine", "sertraline", "paroxetine", "escitalopram", "citalopram"]
            },
            "snri": {
                "structure_type": "Various",
                "chemical_class": "Serotonin-Norepinephrine Reuptake Inhibitors",
                "related": ["venlafaxine", "duloxetine", "desvenlafaxine", "levomilnacipran"]
            },
            "tricyclic": {
                "structure_type": "Tricyclic",
                "chemical_class": "Tricyclic Antidepressants",
                "related": ["amitriptyline", "imipramine", "desipramine", "nortriptyline"]
            },
            "maoi": {
                "structure_type": "Various",
                "chemical_class": "Monoamine Oxidase Inhibitors",
                "related": ["phenelzine", "tranylcypromine", "selegiline", "moclobemide"]
            },

            # Anxiolytics/Hypnotics
            "benzodiazepine": {
                "structure_type": "Benzodiazepine",
                "chemical_class": "GABA Receptor Modulators",
                "related": ["diazepam", "alprazolam", "clonazepam", "lorazepam"]
            },
            "azapirone": {
                "structure_type": "Azapirone",
                "chemical_class": "Serotonin 5-HT1A Receptor Agonists",
                "related": ["buspirone"]
            },

            # Other CNS drugs
            "phenylethylamine": {
                "structure_type": "Phenylethylamine",
                "chemical_class": "Amphetamine Derivatives",
                "related": ["amphetamine", "methylphenidate", "bupropion"]
            }
        }

        # Default values
        structure_type = "Not Specified"
        chemical_class = "Not Specified"
        formula = drug_data.get("identifiers", {}).get("chemical_formula", "Not Available")
        related_compounds = []

        # Try to determine chemical class from drug name or mechanism
        for class_name, class_info in chemical_classes.items():
            # Check if the class name is in the drug name or mechanism
            if class_name in drug_name or class_name in mechanism:
                structure_type = class_info["structure_type"]
                chemical_class = class_info["chemical_class"]
                related_compounds = [{"name": name, "relation_type": "structural analog"} for name in
                                     class_info["related"] if name != drug_name]
                break

            # Also check if any related compounds match
            if any(compound in drug_name for compound in class_info["related"]):
                structure_type = class_info["structure_type"]
                chemical_class = class_info["chemical_class"]
                related_compounds = [{"name": name, "relation_type": "structural analog"} for name in
                                     class_info["related"] if name != drug_name]
                break

        # Special case for brexpiprazole
        if "brexpiprazole" in drug_name:
            structure_type = "Quinolinone Derivative"
            chemical_class = "Benzothiophene-Containing Compounds"
            related_compounds = [
                {"name": "aripiprazole", "relation_type": "structural analog"},
                {"name": "cariprazine", "relation_type": "functional analog"}
            ]

        return {
            "structure_type": structure_type,
            "chemical_class": chemical_class,
            "formula": formula,
            "related_compounds": related_compounds if related_compounds else self._identify_related_compounds(drug_name)
        }

    def _identify_related_compounds(self, drug_name):
        """Identify structurally or functionally related compounds to the drug."""
        # If we couldn't identify related compounds from the chemical class,
        # use some common relationships based on drug name

        # Common classes and their related drugs
        common_relationships = {
            "statin": ["atorvastatin", "simvastatin", "rosuvastatin", "pravastatin", "lovastatin", "fluvastatin",
                       "pitavastatin"],
            "pril": ["enalapril", "lisinopril", "ramipril", "captopril", "benazepril", "perindopril", "quinapril"],
            "sartan": ["losartan", "valsartan", "candesartan", "irbesartan", "telmisartan", "olmesartan"],
            "olol": ["metoprolol", "atenolol", "propranolol", "bisoprolol", "carvedilol", "nebivolol", "timolol"],
            "dipine": ["amlodipine", "nifedipine", "felodipine", "nicardipine", "clevidipine", "nimodipine"],
            "floxacin": ["ciprofloxacin", "levofloxacin", "moxifloxacin", "ofloxacin", "gemifloxacin", "norfloxacin"],
            "cillin": ["amoxicillin", "ampicillin", "penicillin", "nafcillin", "oxacillin", "dicloxacillin"],
            "mycin": ["erythromycin", "azithromycin", "clarithromycin", "clindamycin", "vancomycin", "gentamicin"],
            "cef": ["cefazolin", "ceftriaxone", "cefepime", "cefuroxime", "ceftaroline", "cefdinir"],
            "setron": ["ondansetron", "granisetron", "palonosetron", "dolasetron", "tropisetron"],
            "tidine": ["ranitidine", "famotidine", "cimetidine", "nizatidine"],
            "prazole": ["omeprazole", "esomeprazole", "lansoprazole", "pantoprazole", "rabeprazole"],
            "lukast": ["montelukast", "zafirlukast", "zileuton"]
        }

        related = []
        drug_name_lower = drug_name.lower()

        # Check for common suffixes
        for suffix, drugs in common_relationships.items():
            if suffix in drug_name_lower:
                related = [{"name": name, "relation_type": "same class"} for name in drugs if
                           name.lower() != drug_name_lower]
                if related:
                    break

        # If no suffix match, try to find other relationships based on drug class
        if not related:
            # Add some default relationships based on common drug classes
            if any(term in drug_name_lower for term in ["anti", "anti-", "antibacterial", "antibiotic"]):
                related = [
                    {"name": "amoxicillin", "relation_type": "functional analog"},
                    {"name": "azithromycin", "relation_type": "functional analog"}
                ]
            elif any(term in drug_name_lower for term in ["hypertens", "blood pressure", "cardio", "heart"]):
                related = [
                    {"name": "lisinopril", "relation_type": "functional analog"},
                    {"name": "amlodipine", "relation_type": "functional analog"}
                ]
            elif any(term in drug_name_lower for term in ["psych", "schizo", "antipsychotic"]):
                related = [
                    {"name": "risperidone", "relation_type": "functional analog"},
                    {"name": "olanzapine", "relation_type": "functional analog"}
                ]
            elif any(term in drug_name_lower for term in ["depress", "antidepressant"]):
                related = [
                    {"name": "sertraline", "relation_type": "functional analog"},
                    {"name": "escitalopram", "relation_type": "functional analog"}
                ]
            elif any(term in drug_name_lower for term in ["diabet", "glucose", "insulin"]):
                related = [
                    {"name": "metformin", "relation_type": "functional analog"},
                    {"name": "glipizide", "relation_type": "functional analog"}
                ]
            elif any(term in drug_name_lower for term in ["pain", "analgesic"]):
                related = [
                    {"name": "ibuprofen", "relation_type": "functional analog"},
                    {"name": "acetaminophen", "relation_type": "functional analog"}
                ]
            elif any(term in drug_name_lower for term in ["allerg", "antihist"]):
                related = [
                    {"name": "loratadine", "relation_type": "functional analog"},
                    {"name": "cetirizine", "relation_type": "functional analog"}
                ]
            else:
                # Generic fallback
                related = [
                    {"name": "related compound 1", "relation_type": "potential analog"},
                    {"name": "related compound 2", "relation_type": "potential analog"}
                ]

        return related[:3]  # Limit to 3 related compounds

    def _build_ontological_relationships(self, drug_data):
        """Build ontological relationships for the drug."""
        drug_name = drug_data.get("asset_name", "")
        drug_class = drug_data.get("approval_status", {}).get("drug_class", "")
        manufacturer = drug_data.get("identifiers", {}).get("manufacturer", "")
        indications = drug_data.get("indications", [])
        mechanism = drug_data.get("mechanism_of_action", "")

        # Extract key relationship types from mechanism and indications
        relationships = [
            {"type": "is_a", "subject": drug_name, "object": drug_class or "Pharmaceutical Agent"},
            {"type": "manufactured_by", "subject": drug_name, "object": manufacturer or "Unknown Manufacturer"},
            {"type": "regulated_by", "subject": drug_name, "object": "FDA"}
        ]

        # Add treats relationships for each indication
        for indication in indications:
            relationships.append({
                "type": "treats",
                "subject": drug_name,
                "object": indication
            })

        # Add mechanism relationships based on mechanism text
        mechanism_terms = {
            "dopamine": "Dopamine D2 Receptor",
            "d2": "Dopamine D2 Receptor",
            "serotonin": "Serotonin Receptor",
            "5-ht1a": "Serotonin 5-HT1A Receptor",
            "5-ht2a": "Serotonin 5-HT2A Receptor",
            "adrenergic": "Adrenergic Receptor",
            "alpha1": "Alpha-1 Adrenergic Receptor",
            "alpha2": "Alpha-2 Adrenergic Receptor",
            "histamine": "Histamine Receptor",
            "h1": "Histamine H1 Receptor",
            "muscarinic": "Muscarinic Receptor",
            "gaba": "GABA Receptor",
            "nmda": "NMDA Glutamate Receptor",
            "opioid": "Opioid Receptor"
        }

        for term, receptor in mechanism_terms.items():
            if term.lower() in mechanism.lower():
                relationships.append({
                    "type": "has_target",
                    "subject": drug_name,
                    "object": receptor
                })

        # Add activity relationships
        if "partial agonist" in mechanism.lower():
            relationships.append({
                "type": "has_mechanism",
                "subject": drug_name,
                "object": "Partial Agonism"
            })

        if "antagonist" in mechanism.lower():
            relationships.append({
                "type": "has_mechanism",
                "subject": drug_name,
                "object": "Antagonism"
            })

        if "agonist" in mechanism.lower() and "partial agonist" not in mechanism.lower():
            relationships.append({
                "type": "has_mechanism",
                "subject": drug_name,
                "object": "Agonism"
            })

        if "inhibit" in mechanism.lower() and "reuptake" in mechanism.lower():
            relationships.append({
                "type": "has_mechanism",
                "subject": drug_name,
                "object": "Reuptake Inhibition"
            })

        # Add common adverse effects
        for evidence in drug_data.get("clinical_evidence", []):
            if isinstance(evidence, dict) and "safety" in evidence:
                safety_info = evidence["safety"]
                if isinstance(safety_info, str):
                    for effect in ["akathisia", "weight gain", "sedation", "insomnia", "headache", "nausea",
                                   "dizziness", "constipation", "diarrhea", "fatigue", "rash", "hypotension"]:
                        if effect in safety_info.lower():
                            relationships.append({
                                "type": "has_adverse_effect",
                                "subject": drug_name,
                                "object": effect.title()
                            })

        return relationships

    def _build_semantic_network(self, drug_data):
        """Build a semantic network representation for visualization."""
        drug_name = drug_data.get("asset_name", "")

        # Start building the semantic network
        network = f"[{drug_name}]─┬─"

        # Add drug class
        drug_class = drug_data.get("approval_status", {}).get("drug_class", "")
        if drug_class:
            network += f"[is_a]→[{drug_class}]\n"
            network += "                │─"

        # Add mechanisms
        mechanism = drug_data.get("mechanism_of_action", "")
        mechanisms_added = 0

        if "d2" in mechanism.lower() or "dopamine" in mechanism.lower():
            network += "[acts_on]→[Dopamine D2 Receptor]\n"
            network += "                │─"
            mechanisms_added += 1

        if "5-ht1a" in mechanism.lower() or "serotonin" in mechanism.lower():
            network += "[acts_on]→[Serotonin 5-HT1A Receptor]\n"
            network += "                │─"
            mechanisms_added += 1

        if "5-ht2a" in mechanism.lower() and mechanisms_added < 3:
            network += "[acts_on]→[Serotonin 5-HT2A Receptor]\n"
            network += "                │─"
            mechanisms_added += 1

        # If no mechanisms were added, add a generic one
        if mechanisms_added == 0:
            network += "[has_mechanism]→[Pharmacological Action]\n"
            network += "                │─"

        # Add indications
        indications = drug_data.get("indications", [])
        for i, indication in enumerate(indications[:3]):  # Limit to first 3 for brevity
            indication_short = indication.split("(")[0].strip()
            network += f"[treats]→[{indication_short}]\n                │─"

        # Add metabolism if available
        metabolism_added = False
        for pubmed in drug_data.get("pubmed", []):
            if "metabolized" in pubmed.get("text", "").lower() or "cyp" in pubmed.get("text", "").lower():
                if "cyp3a4" in pubmed.get("text", "").lower() or "3a4" in pubmed.get("text", "").lower():
                    network += "[metabolized_by]→[CYP3A4]\n                "
                    metabolism_added = True
                    if "cyp2d6" in pubmed.get("text", "").lower() or "2d6" in pubmed.get("text", "").lower():
                        network += "└─[metabolized_by]→[CYP2D6]"
                    else:
                        network = network[:-17]  # Remove the last line continuation
                    break
                elif "cyp2d6" in pubmed.get("text", "").lower() or "2d6" in pubmed.get("text", "").lower():
                    network += "[metabolized_by]→[CYP2D6]"
                    metabolism_added = True
                    break

        # If no metabolism info was found, add a generic ending
        if not metabolism_added:
            if network.endswith("│─"):
                network = network[:-17]  # Remove the last line continuation
            else:
                network += "└─[regulated_by]→[FDA]"

        return network


class DrugAssetProfileGenerator:
    """Generates comprehensive asset profiles for pharmaceutical drugs."""

    def __init__(self):
        """Initialize the asset profile generator."""
        self.ontology_builder = DrugOntologyBuilder()

    def generate_asset_profile(self, asset_name, source_data):
        """Generate a comprehensive asset profile for the specified drug."""
        # Start building the profile
        profile = {
            "asset_name": asset_name,
            "identifiers": {},
            "approval_status": {},
            "indications": [],
            "mechanism_of_action": "",
            "clinical_evidence": []
        }

        # Process identifiers
        fda_data = source_data.get("fda_purple_book", {})
        brand_name = fda_data.get("metadata", {}).get("brand_name", asset_name.upper())

        approval_date = "Unknown"
        manufacturer = "Unknown"
        bla_nda = "Unknown"

        # Extract info from FDA data text
        fda_text = fda_data.get("text", "")
        if "Approved by FDA on" in fda_text:
            approval_date = fda_text.split("Approved by FDA on")[1].split(".")[0].strip()
        if "Manufacturer:" in fda_text:
            manufacturer = fda_text.split("Manufacturer:")[1].split(".")[0].strip()
        if "BLA/NDA Number:" in fda_text:
            bla_nda = fda_text.split("BLA/NDA Number:")[1].split(".")[0].strip()

        profile["identifiers"] = {
            "brand_name": brand_name,
            "generic_name": asset_name.lower(),
            "approval_date": approval_date,
            "manufacturer": manufacturer,
            "bla_nda": bla_nda,
            "chemical_formula": "Not Available"  # This would typically come from a chemistry database
        }

        # Process approval status
        status = "Unknown"
        if "Current Regulatory Status:" in fda_text:
            status = fda_text.split("Current Regulatory Status:")[1].strip().rstrip(".")

        # Try to determine drug class from DailyMed data
        daily_med_data = source_data.get("daily_med", {})
        daily_med_text = daily_med_data.get("text", "")

        drug_class = "Pharmaceutical Agent"
        if "antipsychotic" in daily_med_text.lower():
            drug_class = "Atypical Antipsychotic" if "atypical" in daily_med_text.lower() else "Antipsychotic"
        elif "antidepressant" in daily_med_text.lower():
            drug_class = "Antidepressant"
        elif "anxiolytic" in daily_med_text.lower():
            drug_class = "Anxiolytic"
        elif "hypnotic" in daily_med_text.lower() or "sedative" in daily_med_text.lower():
            drug_class = "Sedative-Hypnotic"
        elif "mood stabilizer" in daily_med_text.lower():
            drug_class = "Mood Stabilizer"
        elif "stimulant" in daily_med_text.lower():
            drug_class = "Stimulant"
        elif "anticonvulsant" in daily_med_text.lower() or "antiepileptic" in daily_med_text.lower():
            drug_class = "Anticonvulsant"
        elif "antimicrobial" in daily_med_text.lower() or "antibiotic" in daily_med_text.lower():
            drug_class = "Antimicrobial"
        elif "antiviral" in daily_med_text.lower():
            drug_class = "Antiviral"
        elif "antifungal" in daily_med_text.lower():
            drug_class = "Antifungal"
        elif "antihypertensive" in daily_med_text.lower():
            drug_class = "Antihypertensive"
        elif "antineoplastic" in daily_med_text.lower() or "anticancer" in daily_med_text.lower():
            drug_class = "Antineoplastic"
        elif "anti-inflammatory" in daily_med_text.lower():
            drug_class = "Anti-inflammatory"
        elif "analgesic" in daily_med_text.lower() or "pain" in daily_med_text.lower():
            drug_class = "Analgesic"
        elif "antihistamine" in daily_med_text.lower():
            drug_class = "Antihistamine"
        elif "bronchodilator" in daily_med_text.lower():
            drug_class = "Bronchodilator"

        profile["approval_status"] = {
            "status": status,
            "drug_class": drug_class,
            "type": "New Molecular Entity" if "New Molecular Entity" in fda_text else "Approved Drug"
        }

        # Process indications
        # Extract indications from DailyMed text
        indications = []
        if "indicated for" in daily_med_text.lower():
            ind_text = daily_med_text.split("indicated for")[1].split(".")[0].strip()
            # Split by numbers or bullets
            ind_parts = re.split(r'\d+\.\s*|\•\s*|\*\s*', ind_text)
            for part in ind_parts:
                part = part.strip()
                if part and part not in ["", ":", ";"]:
                    indications.append(part)

        # If no indications found in the standard format, try to extract them differently
        if not indications:
            # Look for "treatment of" or "management of" phrases
            treatment_matches = re.findall(r'treatment of ([^\.;:]+)', daily_med_text, re.IGNORECASE)
            management_matches = re.findall(r'management of ([^\.;:]+)', daily_med_text, re.IGNORECASE)
            therapy_matches = re.findall(r'therapy for ([^\.;:]+)', daily_med_text, re.IGNORECASE)

            for match in treatment_matches + management_matches + therapy_matches:
                if match.strip() not in indications:
                    indications.append(match.strip())

        # If still no indications, use the first sentence of DailyMed text
        if not indications and daily_med_text:
            first_sentence = daily_med_text.split('.')[0]
            if first_sentence:
                indications.append(f"Based on label: {first_sentence}")

        profile["indications"] = indications if indications else ["Indication information not available"]

        # Process mechanism of action
        mechanism = ""
        if "Mechanism of Action" in daily_med_text:
            mech_text = daily_med_text.split("Mechanism of Action:")[1].strip()
            # Take everything up to the next major section
            mechanism = mech_text.split(".")[0] + "."

        # If no mechanism found in the standard format, try to extract it from PubMed data
        if not mechanism:
            for article in source_data.get("pubmed", []):
                article_text = article.get("text", "")
                if any(term in article_text.lower() for term in
                       ["mechanism", "pharmacology", "receptor", "binding", "agonist", "antagonist"]):
                    # Extract relevant sentences
                    sentences = re.split(r'\.', article_text)
                    relevant_sentences = [s for s in sentences if any(term in s.lower() for term in
                                                                      ["mechanism", "pharmacology", "receptor",
                                                                       "binding", "agonist", "antagonist"])]
                    if relevant_sentences:
                        mechanism = '. '.join(relevant_sentences) + '.'
                        break

        profile["mechanism_of_action"] = mechanism if mechanism else "Mechanism of action information not available"

        # Process clinical evidence
        clinical_trials = source_data.get("clinical_trials", [])
        for i, trial in enumerate(clinical_trials):
            trial_text = trial.get("text", "")
            trial_id = trial.get("trial_id", f"Unknown-{i + 1}")

            # Extract phase
            phase = "Unknown"
            phase_match = re.search(r'Phase (\d+)', trial_text, re.IGNORECASE)
            if phase_match:
                phase = f"Phase {phase_match.group(1)}"

            # Extract population
            population = "Unknown"
            if "in" in trial_text and "study" in trial_text:
                population_match = re.search(r'in ([^\.]+)', trial_text)
                if population_match:
                    population = population_match.group(1).strip()

            # Extract results
            results = "Results not available"
            if "Results:" in trial_text:
                results_match = re.search(r'Results: ([^\.]+)', trial_text)
                if results_match:
                    results = results_match.group(1).strip()

            # Extract safety information
            safety = "Safety information not available"
            if "Safety:" in trial_text:
                safety_match = re.search(r'Safety: ([^\.]+)', trial_text)
                if safety_match:
                    safety = safety_match.group(1).strip()

            # If no specific safety information, look for common terms
            if safety == "Safety information not available":
                common_adverse_events = ["adverse", "reaction", "side effect", "tolerability"]
                for term in common_adverse_events:
                    if term in trial_text.lower():
                        safety_section = trial_text.split(term)[1].split(".")[0]
                        if safety_section:
                            safety = f"Adverse effects may include: {safety_section.strip()}"
                            break

            profile["clinical_evidence"].append({
                "trial_name": f"Study {trial_id}",
                "phase": phase,
                "population": population,
                "key_results": results,
                "safety": safety
            })

        # If no clinical trials were found, add a placeholder
        if not profile["clinical_evidence"]:
            profile["clinical_evidence"].append({
                "trial_name": "No specific trial information available",
                "phase": "Unknown",
                "population": "Unknown",
                "key_results": "No results data available",
                "safety": "No safety data available"
            })

        # Build ontology and taxonomy
        drug_ontology = self.ontology_builder.build_ontology(profile)
        profile["ontology"] = drug_ontology

        # Format the final profile
        return self._format_profile(profile)

    def _format_profile(self, profile):
        """Format the asset profile for presentation."""
        formatted = {
            "Asset Profile": profile["asset_name"],
            "Identifiers": {
                "Brand Name": profile["identifiers"].get("brand_name", ""),
                "Generic Name": profile["identifiers"].get("generic_name", ""),
                "Approval Date": profile["identifiers"].get("approval_date", ""),
                "Manufacturer": profile["identifiers"].get("manufacturer", ""),
                "BLA/NDA Number": profile["identifiers"].get("bla_nda", ""),
                "Chemical Formula": profile["identifiers"].get("chemical_formula", "")
            },
            "Approval Status": {
                "Status": profile["approval_status"].get("status", ""),
                "Drug Class": profile["approval_status"].get("drug_class", ""),
                "Type": profile["approval_status"].get("type", "")
            },
            "Indications & Usage": profile["indications"],
            "Mechanism of Action": profile["mechanism_of_action"],
            "Clinical Evidence Summary": profile["clinical_evidence"],
            "Drug Ontology": profile.get("ontology", {})
        }

        return formatted

    def visualize_drug_ontology(self, drug_name, ontology_data):
        """
        Generate a visualization of the drug ontology.
        Returns an ASCII diagram
        """
        # Create an ASCII art representation of the ontology
        drug_class = ontology_data.get("classifications", {}).get("pharmaceutical", {}).get("family", "")

        # Get indications
        therapeutic = ontology_data.get("classifications", {}).get("therapeutic", {})
        indications = []
        for area, conditions in therapeutic.items():
            for condition in conditions:
                indications.append(condition.split("(")[0].strip())

        # Get top 3 indications
        top_indications = indications[:3] if indications else ["N/A"]

        # Get targets
        targets = ontology_data.get("classifications", {}).get("pharmacological", {}).get("targets", [])
        target_list = []
        for target in targets:
            receptor = target.get("receptor", "")
            activity = target.get("activity", "")
            target_list.append(f"{receptor} ({activity[:3]})")

        # Get top 3 targets
        top_targets = target_list[:3] if target_list else ["N/A"]

        # Get chemical class
        chem_class = ontology_data.get("classifications", {}).get("chemical", {})
        structure = chem_class.get("structure_type", "N/A")

        # Create diagram
        ascii_diagram = f"""
                                         +------{drug_name}------+
                                         |                       |
                  +---------------------+|+--------------------+ |
                  |                      |                     | |
        +---------v---------+   +--------v--------+   +--------v--------+
        |    Drug Class     |   |   Indications   |   |    Mechanism    |
        | {drug_class.ljust(17)} |   | • {top_indications[0][:15].ljust(15)} |   | • {top_targets[0][:15].ljust(15)} |
        |                   |   | • {(top_indications[1][:15] if len(top_indications) > 1 else "").ljust(15)} |   | • {(top_targets[1][:15] if len(top_targets) > 1 else "").ljust(15)} |
        +---------+---------+   | • {(top_indications[2][:15] if len(top_indications) > 2 else "").ljust(15)} |   | • {(top_targets[2][:15] if len(top_targets) > 2 else "").ljust(15)} |
                  |             +-------+--------+    +-------+--------+
                  |                     |                     |
        +---------v---------+   +-------v--------+   +-------v--------+
        | Chemical Family   |   | Side Effects   |   | Metabolism     |
        | {structure.ljust(17)} |   | • Various      |   | • CYP Enzymes  |
        |                   |   |                |   |                |
        +-------------------+   +----------------+   +----------------+

        """

        return ascii_diagram


def generate_asset_markdown(profile, visualization):
    """Generate a markdown representation of the asset profile."""

    # Start with the title
    markdown_text = f"# {profile['Asset Profile']} Asset Profile\n\n"

    # Add identifiers section
    identifiers = profile["Identifiers"]
    markdown_text += "## Identifiers\n\n"
    markdown_text += f"**Brand Name:** {identifiers['Brand Name']}  \n"
    markdown_text += f"**Generic Name:** {identifiers['Generic Name']}  \n"
    markdown_text += f"**Approval Date:** {identifiers['Approval Date']}  \n"
    markdown_text += f"**Manufacturer:** {identifiers['Manufacturer']}  \n"
    markdown_text += f"**BLA/NDA Number:** {identifiers['BLA/NDA Number']}  \n"
    markdown_text += f"**Chemical Formula:** {identifiers['Chemical Formula']}  \n\n"

    # Add approval status
    status = profile["Approval Status"]
    markdown_text += "## Approval Status\n\n"
    markdown_text += f"**Status:** {status['Status']}  \n"
    markdown_text += f"**Drug Class:** {status['Drug Class']}  \n"
    markdown_text += f"**Type:** {status['Type']}  \n\n"

    # Add indications
    markdown_text += "## Indications & Usage\n\n"
    for indication in profile["Indications & Usage"]:
        markdown_text += f"- {indication}\n"
    markdown_text += "\n"

    # Add mechanism of action
    markdown_text += "## Mechanism of Action\n\n"
    markdown_text += f"{profile['Mechanism of Action']}\n\n"

    # Add clinical evidence
    markdown_text += "## Clinical Evidence Summary\n\n"
    for i, evidence in enumerate(profile["Clinical Evidence Summary"], 1):
        markdown_text += f"### {evidence['trial_name']}\n\n"
        markdown_text += f"**Phase:** {evidence['phase']}  \n"
        markdown_text += f"**Population:** {evidence['population']}  \n"
        markdown_text += f"**Key Results:** {evidence['key_results']}  \n"
        markdown_text += f"**Safety:** {evidence['safety']}  \n\n"

    # Add ontology visualization
    markdown_text += "## Drug Ontology\n\n"
    markdown_text += "### Visualization\n\n"
    markdown_text += "```\n" + visualization + "\n```\n\n"

    # Add classification hierarchy
    ont = profile["Drug Ontology"]["classifications"]
    markdown_text += "### Classification Hierarchy\n\n"

    markdown_text += "#### Pharmaceutical Classification\n\n"
    pharm = ont["pharmaceutical"]
    markdown_text += f"- **Class:** {pharm['class']}\n"
    markdown_text += f"- **Subclass:** {pharm['subclass']}\n"
    markdown_text += f"- **Family:** {pharm['family']}\n"
    markdown_text += f"- **Subfamily:** {pharm['subfamily']}\n"
    markdown_text += f"- **Type:** {pharm['type']}\n"
    markdown_text += f"- **Agent:** {pharm['agent']}\n\n"

    markdown_text += "#### Pharmacological Classification\n\n"
    markdown_text += f"- **Primary Mechanism:** {ont['pharmacological']['primary_mechanism']}\n"
    markdown_text += "- **Targets:**\n"
    for target in ont["pharmacological"]["targets"]:
        markdown_text += f"  - {target['receptor']} ({target['family']}): {target['activity']}\n"
    markdown_text += "\n"

    markdown_text += "#### Therapeutic Classification\n\n"
    for area, conditions in ont["therapeutic"].items():
        markdown_text += f"- **{area}:**\n"
        for condition in conditions:
            markdown_text += f"  - {condition}\n"
    markdown_text += "\n"

    markdown_text += "#### Chemical Classification\n\n"
    chem = ont["chemical"]
    markdown_text += f"- **Structure Type:** {chem['structure_type']}\n"
    markdown_text += f"- **Chemical Class:** {chem['chemical_class']}\n"
    markdown_text += f"- **Formula:** {chem['formula']}\n"
    markdown_text += "- **Related Compounds:**\n"
    for compound in chem["related_compounds"]:
        markdown_text += f"  - {compound['name']} ({compound['relation_type']})\n"
    markdown_text += "\n"

    # Add relationships
    markdown_text += "### Ontological Relationships\n\n"
    relationships = profile["Drug Ontology"]["relationships"]

    # Group relationships by type
    rel_by_type = {}
    for rel in relationships:
        rel_type = rel["type"]
        if rel_type not in rel_by_type:
            rel_by_type[rel_type] = []
        rel_by_type[rel_type].append(rel)

    # Display relationships by type
    for rel_type, rels in rel_by_type.items():
        markdown_text += f"#### {rel_type.replace('_', ' ').title()}\n\n"
        for rel in rels:
            markdown_text += f"- {rel['subject']} → {rel['object']}\n"
        markdown_text += "\n"

    # Add semantic network
    markdown_text += "### Semantic Network\n\n"
    markdown_text += "```\n" + profile["Drug Ontology"]["semantic_network"] + "\n```\n\n"

    return markdown_text
