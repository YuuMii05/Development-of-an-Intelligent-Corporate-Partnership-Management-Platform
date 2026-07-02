import os
import ollama
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 12 new Huawei partners located in Tunisia (from the official partner directory screenshots).
# Metrics (health_score, risk_level, engagement_trend, future_value_estimate) are DEMO values.
new_partners = [
    {"company_name": "Smart Tunisia", "industry": "IT Distribution & Collaboration",
     "objectives": "Gold Distribution Partner specialized in Data Communication-Basic and Intelligent Collaboration-Basic solutions distribution across Tunisia.",
     "health_score": 90, "risk_level": "Low", "engagement_trend": "Growing", "future_value_estimate": "$350K (Strong)"},
    {"company_name": "Computer Distribution S.A", "industry": "IT Distribution & System Integration",
     "objectives": "Authorized Reseller and Gold Distribution Partner delivering Data Communication-Basic, Storage-Basic and Enterprise Services and Software-Basic distribution and integration.",
     "health_score": 87, "risk_level": "Low", "engagement_trend": "Growing", "future_value_estimate": "$280K (Strong)"},
    {"company_name": "EASYTEK", "industry": "IT Solutions & Reselling",
     "objectives": "Authorized Reseller delivering Huawei enterprise IT products and localized solution reselling.",
     "health_score": 66, "risk_level": "Medium", "engagement_trend": "Stable", "future_value_estimate": "$90K (Regular)"},
    {"company_name": "HES Tunisie", "industry": "Enterprise Hardware & Services",
     "objectives": "Authorized Reseller providing Huawei enterprise hardware, infrastructure, and services.",
     "health_score": 72, "risk_level": "Low", "engagement_trend": "Stable", "future_value_estimate": "$110K (Regular)"},
    {"company_name": "Network Associates", "industry": "Networking & Infrastructure",
     "objectives": "Authorized Reseller focused on networking and enterprise infrastructure deployments.",
     "health_score": 58, "risk_level": "Medium", "engagement_trend": "Declining", "future_value_estimate": "$70K (To Monitor)"},
    {"company_name": "OPENYX", "industry": "Data Communication Solutions",
     "objectives": "Authorized Reseller specialized in Data Communication-Basic routing and networking solutions.",
     "health_score": 69, "risk_level": "Medium", "engagement_trend": "Stable", "future_value_estimate": "$85K (Regular)"},
    {"company_name": "SIMOP Tunisie", "industry": "ICT Training & Integration",
     "objectives": "Authorized Reseller and Certified Huawei Authorized Learning Partner delivering ICT training and integration services.",
     "health_score": 84, "risk_level": "Low", "engagement_trend": "Growing", "future_value_estimate": "$200K (Strong)"},
    {"company_name": "STE Standard Sharing Software (3S)", "industry": "Software & Storage Solutions",
     "objectives": "Authorized Reseller specialized in Data Communication-Basic, Storage-Advanced and Enterprise Services and Software-Basic solutions.",
     "health_score": 80, "risk_level": "Low", "engagement_trend": "Growing", "future_value_estimate": "$160K (Solid)"},
    {"company_name": "TELCOTEC Integration", "industry": "Telecom & Systems Integration",
     "objectives": "Authorized Reseller focused on telecom and enterprise systems integration.",
     "health_score": 63, "risk_level": "Medium", "engagement_trend": "Stable", "future_value_estimate": "$75K (Regular)"},
    {"company_name": "Tunisys", "industry": "Enterprise IT Services",
     "objectives": "Authorized Reseller providing enterprise IT services and Huawei solution reselling.",
     "health_score": 76, "risk_level": "Low", "engagement_trend": "Stable", "future_value_estimate": "$130K (Regular)"},
    {"company_name": "Waycon", "industry": "IT Infrastructure & Consulting",
     "objectives": "Authorized Reseller delivering IT infrastructure, consulting, and Huawei solution provisioning.",
     "health_score": 55, "risk_level": "Medium", "engagement_trend": "Declining", "future_value_estimate": "$60K (To Monitor)"},
    {"company_name": "Carthage", "industry": "IT Solutions & Reselling",
     "objectives": "Authorized Reseller providing Huawei enterprise IT products and localized services.",
     "health_score": 68, "risk_level": "Medium", "engagement_trend": "Stable", "future_value_estimate": "$80K (Regular)"},
]


def main():
    # Fetch existing names to avoid duplicates
    existing = supabase.table("partner_profiles").select("company_name").execute()
    existing_names = {r["company_name"].strip().lower() for r in (existing.data or [])}
    print(f"Existing partners in DB: {len(existing_names)}")

    inserted = 0
    for p in new_partners:
        if p["company_name"].strip().lower() in existing_names:
            print(f"  SKIP (already exists): {p['company_name']}")
            continue

        combined_text = f"{p['company_name']} {p['industry']} {p['objectives']}"
        print(f"  Generating embedding for: {p['company_name']} ...")
        emb = ollama.embeddings(model="nomic-embed-text", prompt=combined_text)["embedding"]

        supabase.table("partner_profiles").insert({
            "company_name": p["company_name"],
            "industry": p["industry"],
            "objectives": p["objectives"],
            "embedding": emb,
            "health_score": p["health_score"],
            "risk_level": p["risk_level"],
            "engagement_trend": p["engagement_trend"],
            "future_value_estimate": p["future_value_estimate"],
        }).execute()
        print(f"    Inserted: {p['company_name']}")
        inserted += 1

    total = supabase.table("partner_profiles").select("id", count="exact").execute()
    print(f"\nDone. Inserted {inserted} new partners. Total rows now: {total.count}")


if __name__ == "__main__":
    main()
