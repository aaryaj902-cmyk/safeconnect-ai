"""
Generates data/companies.csv -- a registry of companies used for recruiter /
company verification lookups.

Includes:
  - A set of well-known REAL company names (public, factual, non-sensitive
    information: name + industry + HQ + domain pattern + founded year) so
    that searches for actual companies like "Google" or "Microsoft" resolve
    to a verified, high-trust record.
  - A larger set of realistic SMALL/MID-SIZE legitimate companies (synthetic
    but plausible) to populate the "verified" pool.
  - A set of KNOWN SCAM / high-risk shell company names (synthetic, modeled
    on common recruitment-scam company naming patterns: generic "staffing/
    hiring/talent" words, no real domain, no LinkedIn presence) to populate
    the "flagged" pool that the recruiter verification + scam ledger
    features query against.
"""
import csv
import os
import random

random.seed(7)

REAL_COMPANIES = [
    ("Google", "Internet", "Mountain View, CA, US", "google.com", 1998),
    ("Microsoft", "Computer Software", "Redmond, WA, US", "microsoft.com", 1975),
    ("Amazon", "Internet/Retail", "Seattle, WA, US", "amazon.com", 1994),
    ("Meta Platforms", "Internet", "Menlo Park, CA, US", "meta.com", 2004),
    ("Apple", "Consumer Electronics", "Cupertino, CA, US", "apple.com", 1976),
    ("Netflix", "Media Production", "Los Gatos, CA, US", "netflix.com", 1997),
    ("Salesforce", "Computer Software", "San Francisco, CA, US", "salesforce.com", 1999),
    ("IBM", "Information Technology and Services", "Armonk, NY, US", "ibm.com", 1911),
    ("Adobe", "Computer Software", "San Jose, CA, US", "adobe.com", 1982),
    ("Oracle", "Computer Software", "Austin, TX, US", "oracle.com", 1977),
    ("Accenture", "Management Consulting", "Dublin, IE", "accenture.com", 1989),
    ("Deloitte", "Management Consulting", "London, GB", "deloitte.com", 1845),
    ("Infosys", "Information Technology and Services", "Bangalore, KA, IN", "infosys.com", 1981),
    ("Tata Consultancy Services", "Information Technology and Services", "Mumbai, MH, IN", "tcs.com", 1968),
    ("Wipro", "Information Technology and Services", "Bangalore, KA, IN", "wipro.com", 1945),
    ("HCLTech", "Information Technology and Services", "Noida, UP, IN", "hcltech.com", 1976),
    ("JPMorgan Chase", "Banking", "New York, NY, US", "jpmorganchase.com", 1799),
    ("Goldman Sachs", "Financial Services", "New York, NY, US", "goldmansachs.com", 1869),
    ("Spotify", "Media Production", "Stockholm, SE", "spotify.com", 2006),
    ("Shopify", "Computer Software", "Ottawa, ON, CA", "shopify.com", 2006),
    ("Stripe", "Financial Services", "San Francisco, CA, US", "stripe.com", 2010),
    ("Atlassian", "Computer Software", "Sydney, NSW, AU", "atlassian.com", 2002),
    ("SAP", "Computer Software", "Walldorf, DE", "sap.com", 1972),
    ("Siemens", "Industrial Automation", "Munich, DE", "siemens.com", 1847),
    ("Unilever", "Consumer Goods", "London, GB", "unilever.com", 1929),
    ("Procter & Gamble", "Consumer Goods", "Cincinnati, OH, US", "pg.com", 1837),
    ("LinkedIn", "Internet", "Sunnyvale, CA, US", "linkedin.com", 2002),
    ("Intel", "Semiconductors", "Santa Clara, CA, US", "intel.com", 1968),
    ("NVIDIA", "Semiconductors", "Santa Clara, CA, US", "nvidia.com", 1993),
    ("Cisco Systems", "Networking", "San Jose, CA, US", "cisco.com", 1984),
]

LEGIT_PREFIXES = [
    "Apex", "Northbridge", "Summit", "Bluepeak", "Crestview", "Lakeside", "Meridian",
    "Horizon", "Stonefield", "Brightwater", "Ironwood", "Cascade", "Pinecrest", "Westgate",
    "Harborview", "Redwood", "Glenmark", "Fairview", "Atlas", "Vantage", "Clearwater",
    "Oakmont", "Silverline", "Brookstone", "Eastview", "Sterling", "Granite", "Pacific Crest",
]
LEGIT_SUFFIXES = [
    "Technologies", "Solutions", "Consulting", "Industries", "Group", "Partners",
    "Systems", "Logistics", "Healthcare", "Financial", "Retail Co.", "Manufacturing",
    "Media", "Labs", "Networks", "Analytics", "Capital", "Holdings",
]
INDUSTRIES = [
    "Information Technology and Services", "Computer Software", "Financial Services",
    "Hospital & Health Care", "Marketing and Advertising", "Retail", "Construction",
    "Real Estate", "Education Management", "Logistics and Supply Chain",
    "Human Resources", "Insurance", "Telecommunications", "Manufacturing",
]
LOCATIONS = [
    "New York, NY, US", "San Francisco, CA, US", "Austin, TX, US", "Chicago, IL, US",
    "Seattle, WA, US", "Boston, MA, US", "Denver, CO, US", "Atlanta, GA, US",
    "London, England, GB", "Manchester, England, GB", "Toronto, ON, CA",
    "Bangalore, KA, IN", "Mumbai, MH, IN", "Pune, MH, IN", "Sydney, NSW, AU",
]

SCAM_COMPANY_NAMES = [
    ("Global Hire Express", "Staffing and Recruiting"),
    ("QuickJobs International", "Staffing and Recruiting"),
    ("WorkFromHome Solutions LLC", "Staffing and Recruiting"),
    ("Premier Remote Staffing", "Staffing and Recruiting"),
    ("FastTrack Employment Group", "Staffing and Recruiting"),
    ("EasyHire Worldwide", "Staffing and Recruiting"),
    ("Remote Talent Connect", "Staffing and Recruiting"),
    ("Global Career Network", "Staffing and Recruiting"),
    ("PayDay Staffing Co.", "Staffing and Recruiting"),
    ("Instant Hire Agency", "Staffing and Recruiting"),
    ("WorldWide Remote Jobs", "Staffing and Recruiting"),
    ("TalentBridge Express", "Staffing and Recruiting"),
    ("Global Talent Solutions Inc.", "Staffing and Recruiting"),
    ("Staffing Today", "Staffing and Recruiting"),
    ("HireFast Global", "Staffing and Recruiting"),
]

# A few extra explicitly-named legitimate demo companies referenced in the
# original design mockups, so trying these in the live demo resolves the
# same way the mockup screens depict.
EXTRA_VERIFIED_DEMO_COMPANIES = [
    ("XYZ Tech", "Information Technology and Services", "Austin, TX, US", "xyztech.com", 2011),
    ("Verified Tech Startup", "Computer Software", "San Francisco, CA, US", "verifiedtechstartup.com", 2018),
    ("Global Tech Solutions", "Information Technology and Services", "Chicago, IL, US", "globaltechsolutions.com", 2009),
]


def main():
    rows = []
    cid = 1

    for name, industry, hq, domain, founded in REAL_COMPANIES:
        rows.append({
            "company_id": cid, "name": name, "industry": industry, "headquarters": hq,
            "official_domain": domain, "founded_year": founded, "trust_status": "verified",
            "trust_score": random.randint(92, 99), "employee_count": random.choice(
                [5000, 10000, 25000, 50000, 100000, 200000]),
            "report_count": 0, "notes": "Publicly known, established company.",
        })
        cid += 1

    for name, industry, hq, domain, founded in EXTRA_VERIFIED_DEMO_COMPANIES:
        rows.append({
            "company_id": cid, "name": name, "industry": industry, "headquarters": hq,
            "official_domain": domain, "founded_year": founded, "trust_status": "verified",
            "trust_score": random.randint(82, 94), "employee_count": random.choice([80, 150, 300]),
            "report_count": 0, "notes": "Registered business with verifiable domain and presence.",
        })
        cid += 1

    for _ in range(400):
        name = f"{random.choice(LEGIT_PREFIXES)} {random.choice(LEGIT_SUFFIXES)}"
        rows.append({
            "company_id": cid, "name": name, "industry": random.choice(INDUSTRIES),
            "headquarters": random.choice(LOCATIONS),
            "official_domain": name.lower().replace(" ", "").replace(".", "").replace(",", "") + ".com",
            "founded_year": random.randint(1985, 2020), "trust_status": "verified",
            "trust_score": random.randint(70, 96),
            "employee_count": random.choice([10, 25, 50, 120, 300, 800, 1500]),
            "report_count": 0, "notes": "Registered business with verifiable domain and presence.",
        })
        cid += 1

    for name, industry in SCAM_COMPANY_NAMES:
        rows.append({
            "company_id": cid, "name": name, "industry": industry,
            "headquarters": "Unverified / Remote",
            "official_domain": "", "founded_year": random.randint(2022, 2026),
            "trust_status": "flagged",
            "trust_score": random.randint(5, 28),
            "employee_count": random.choice([0, 1, 2, 5]),
            "report_count": random.randint(15, 450),
            "notes": "Multiple community fraud reports; no verifiable corporate registration found.",
        })
        cid += 1

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "companies.csv")
    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} companies to {out_path}")
    print(f"Verified: {sum(1 for r in rows if r['trust_status']=='verified')}, "
          f"Flagged: {sum(1 for r in rows if r['trust_status']=='flagged')}")


if __name__ == "__main__":
    main()
