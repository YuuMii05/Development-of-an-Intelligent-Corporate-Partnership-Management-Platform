import ollama
import os
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environmental configurations
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print(" ERROR: Missing environmental variables! Check your .env file setup.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

partners_data = [
    {
        "company_name": "Tunisie Micro Informatique (TMI)",
        "industry": "Enterprise IT & Solutions Architecture",
        "objectives": "Certified Huawei Authorized Learning Partner. Diamond Reseller specializing in Data Communication Master setups, Storage Master cluster file structures, and Enterprise Services and Software-Master architectures."
    },
    {
        "company_name": "Prologic Tunisie",
        "industry": "Enterprise IT & System Integration",
        "objectives": "Gold Reseller tier provider specializing in System Integration, Data Communication-Advanced routing infrastructure, Storage-Advanced high availability pools, Optical-Basic pathways, and Enterprise Services and Software-Basic."
    },
    {
        "company_name": "STE Autonomous Systems Engineering",
        "industry": "Systems Engineering & Automation",
        "objectives": "Gold Reseller ecosystem partner specializing in advanced Automation systems, Systems Engineering frameworks, Data Communication-Basic setups, Optical-Advanced transport channels, and Enterprise Services and Software-Basic clusters."
    },
    {
        "company_name": "ACT",
        "industry": "Advanced Computer Technologies",
        "objectives": "Authorized Reseller network node specializing in Advanced Computer Technologies and verified local Infrastructure node resource deployments."
    },
    {
        "company_name": "ADACTIM",
        "industry": "Managed Services & Cloud Integration",
        "objectives": "Authorized Reseller agency focused on Managed Services delivery, Cloud Integration architecture, and localized structural Solution Integrator services."
    },
    {
        "company_name": "BITS",
        "industry": "Business Information Technology Solutions",
        "objectives": "Authorized Reseller center maximizing Business Information Technology Solutions, Data Communication-Advanced configurations, Storage-Advanced environments, and Enterprise Services and Software-Basic engines."
    },
    {
        "company_name": "BLUE IT",
        "industry": "Enterprise Architecture & Provisioning",
        "objectives": "Authorized Reseller specialist optimizing localized Enterprise Architecture systems, platform Provisioning paths, and core infrastructure node deployments."
    }
]

async def seed_database():
    print(" Initiating Supabase connection sync lifecycle...")
    
    try:
        # 1. Clear out stale records to prevent row key collisions
        print(" Clearing out old profile rows from public.partner_profiles...")
        supabase.table("partner_profiles").delete().neq("company_name", "").execute()
        
        # 2. Loop and generate vectors via Ollama processing
        print(" Pushing real partner profiles up to your Supabase cloud data grid...")
        for partner in partners_data:
            # Create a string representation to build vector weights against
            combined_text = f"{partner['company_name']} {partner['industry']} {partner['objectives']}"
            
            print(f" Generating 768-dim embeddings via Ollama for: {partner['company_name']}...")
            
            # Call Ollama to generate real math vector coordinates using the 768-dimension model
            response_embed = ollama.embeddings(
                model="nomic-embed-text", 
                prompt=combined_text
            )
            real_vector = response_embed["embedding"]
            
            # Insert the complete row with real text and real mathematical vectors into Supabase
            response = supabase.table("partner_profiles").insert({
                "company_name": partner["company_name"],
                "industry": partner["industry"],
                "objectives": partner["objectives"],
                "embedding": real_vector
            }).execute()
            
            print(f"    Successfully seeded: {partner['company_name']}")

        print("\n Database fully initialized with real vector alignments!")
        
    except Exception as e:
        print(f" DATABASE UPDATE EXCEPTION TRACE: {str(e)}")

if __name__ == "__main__":
    asyncio.run(seed_database())