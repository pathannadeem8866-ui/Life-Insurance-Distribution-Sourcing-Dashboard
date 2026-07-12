import pandas as pd
import numpy as np
from pathlib import Path


def clean_insurance_data(base_dir=None):
    base_path = Path(base_dir).resolve() if base_dir is not None else Path(__file__).resolve().parent
    base_path.mkdir(parents=True, exist_ok=True)

    print("Starting Data Cleaning Pipeline...\n")

    # 1. LOAD THE RAW DATA
    raw_agents_path = base_path / 'raw_agents_data.csv'
    raw_policies_path = base_path / 'raw_policies_data.csv'

    if not raw_agents_path.exists() or not raw_policies_path.exists():
        raise FileNotFoundError(
            f"Required raw files were not found in {base_path}. "
            f"Expected {raw_agents_path.name} and {raw_policies_path.name}."
        )

    print(f"Loading raw CSV files from {base_path}...")
    df_agents = pd.read_csv(raw_agents_path)
    df_policies = pd.read_csv(raw_policies_path)

    print("\nAgents dataset overview:")
    df_agents.info()
    print("\nAgents dataset preview:")
    print(df_agents.head().to_string(index=False))

    print("\nPolicies dataset overview:")
    df_policies.info()
    print("\nPolicies dataset preview:")
    print(df_policies.head().to_string(index=False))

    print(f"Initial Agents shape: {df_agents.shape}")
    print(f"Initial Policies shape: {df_policies.shape}\n")

    # ==========================================
    # 2. CLEANING AGENTS DATA
    # ==========================================
    print("Cleaning Agents Data...")
    
    # A. Standardize Text Formatting
    # Convert everything to title case and strip accidental whitespace
    df_agents['Agent_Name'] = df_agents['Agent_Name'].fillna('').astype(str).str.strip().str.title()
    df_agents['Status'] = df_agents['Status'].fillna('Unknown').astype(str).str.strip().str.title()

    # B. Standardize Sourcing Channels using a Mapping Dictionary
    channel_mapping = {
        'ref': 'Referral', 'referral': 'Referral', 'employee referral': 'Referral',
        'linkedin': 'LinkedIn', 'linked in': 'LinkedIn', 'li': 'LinkedIn',
        'walk in': 'Walk-in', 'walkin': 'Walk-in', 'direct walkin': 'Walk-in', 'walk-in': 'Walk-in',
        'agency': 'Agency Partner', 'partner broker': 'Agency Partner', 'agency partner': 'Agency Partner',
        'naukri': 'Job Portal', 'indeed': 'Job Portal', 'portal': 'Job Portal', 'job portal': 'Job Portal'
    }
    normalized_channel = df_agents['Sourcing_Channel'].fillna('Unknown').astype(str).str.strip().str.lower()
    df_agents['Sourcing_Channel'] = normalized_channel.map(channel_mapping).fillna(
        df_agents['Sourcing_Channel'].fillna('Unknown').astype(str).str.strip().str.title()
    )

    # C. Handle Missing Values (Nulls) in Recruitment Cost
    # We will replace missing costs with 0 to assume no direct cost was recorded
    missing_costs = df_agents['Recruitment_Cost'].isna().sum()
    df_agents['Recruitment_Cost'] = df_agents['Recruitment_Cost'].fillna(0).astype(int)
    print(f"  -> Fixed {missing_costs} missing recruitment costs.")

    # D. Parse Dates
    df_agents['Onboarding_Date'] = pd.to_datetime(df_agents['Onboarding_Date'], errors='coerce')


    # ==========================================
    # 3. CLEANING POLICIES DATA
    # ==========================================
    print("\nCleaning Policies Data...")

    # A. Remove Duplicates
    initial_policy_count = len(df_policies)
    df_policies = df_policies.drop_duplicates(subset=['Policy_ID'])
    print(f"  -> Removed {initial_policy_count - len(df_policies)} duplicate rows.")

    # B. Clean Premium Amount (Extract numbers using regex and cast to integer)
    # This removes 'INR', '/-', and spaces, leaving just the digits
    df_policies['Premium_Amount'] = df_policies['Premium_Amount'].astype(str).str.replace(r'[^\d]', '', regex=True)
    df_policies['Premium_Amount'] = pd.to_numeric(df_policies['Premium_Amount'], errors='coerce').fillna(0).astype(int)

    # C. Handle Missing Values in Status
    missing_status = df_policies['Status'].isna().sum()
    df_policies['Status'] = df_policies['Status'].fillna('Unknown').astype(str).str.strip().str.title()
    print(f"  -> Filled {missing_status} missing policy statuses.")

    # D. Parse Dates
    df_policies['Issue_Date'] = pd.to_datetime(df_policies['Issue_Date'], errors='coerce')


    # ==========================================
    # 4. FIX LOGICAL ERRORS (Time Paradoxes)
    # ==========================================
    print("\nAuditing Logical Integrity (Dates)...")
    
    # Temporarily merge onboarding date into policies to compare while preserving original policy row indices
    df_merged = df_policies.reset_index().merge(
        df_agents[['Agent_ID', 'Onboarding_Date']],
        on='Agent_ID',
        how='left',
        sort=False,
    )

    # Identify paradoxes: Policy issued BEFORE agent was onboarded
    paradox_mask = df_merged['Issue_Date'] < df_merged['Onboarding_Date']
    paradox_count = int(paradox_mask.sum())

    # Fix: If a paradox exists, set the policy Issue_Date to match the Agent's Onboarding_Date
    if paradox_count > 0:
        policy_indices = df_merged.loc[paradox_mask, 'index']
        df_policies.loc[policy_indices, 'Issue_Date'] = df_merged.loc[paradox_mask, 'Onboarding_Date'].values
    print(f"  -> Corrected {paradox_count} timeline paradoxes (Policy predates Agent).")


    # ==========================================
    # 5. EXPORT CLEAN DATA
    # ==========================================
    print("\nExporting clean datasets...")
    df_agents.to_csv(base_path / 'clean_agents_data.csv', index=False)
    df_policies.to_csv(base_path / 'clean_policies_data.csv', index=False)
    
    print(f"Final Agents shape: {df_agents.shape}")
    print(f"Final Policies shape: {df_policies.shape}")
    print("Pipeline Complete! Files are ready for SQL and Power BI/Tableau.")

if __name__ == "__main__":
    clean_insurance_data()