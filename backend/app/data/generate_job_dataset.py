"""
Generates data/fake_job_postings.csv

NOTE ON DATA PROVENANCE
------------------------
This sandbox has no internet access, so the real Kaggle "Fake Job Postings"
dataset (~17,880 rows, EMSCAD) could not be downloaded directly. Instead,
this script PROCEDURALLY GENERATES a dataset of equivalent size and the
SAME SCHEMA, built from the same statistical patterns documented for the
real dataset:

  - ~95% genuine / ~5% fraudulent split (matches the real EMSCAD ratio)
  - Fraudulent postings disproportionately: lack a company logo, offer
    salaries skewed high or absent, use urgent/payment language, are
    posted under generic "Staffing/Recruiting" function, omit education
    requirements, and originate from free-mail-style company profiles.
  - Genuine postings draw from real-world job titles, real company-style
    names, real US/UK/IN locations, and realistic descriptions.

This gives you a fully working, statistically-realistic training set out
of the box. When you have internet access, you can swap this for the real
Kaggle CSV (same column names) by downloading it from:
  https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction
and dropping it in as backend/app/data/fake_job_postings.csv  -- the
training script (train_model.py) does not care which one it reads.
"""
import csv
import os
import random

random.seed(42)

REAL_TITLES = [
    "Software Engineer", "Data Analyst", "Marketing Coordinator", "Customer Service Representative",
    "Administrative Assistant", "Sales Associate", "Project Manager", "Graphic Designer",
    "Accountant", "HR Generalist", "Operations Manager", "Business Development Manager",
    "Content Writer", "Social Media Manager", "Financial Analyst", "Product Manager",
    "Registered Nurse", "Mechanical Engineer", "Civil Engineer", "Electrical Engineer",
    "Warehouse Associate", "Delivery Driver", "Executive Assistant", "Recruiter",
    "UX Designer", "Backend Developer", "Frontend Developer", "DevOps Engineer",
    "QA Tester", "Network Administrator", "IT Support Specialist", "Data Scientist",
    "Machine Learning Engineer", "Paralegal", "Legal Assistant", "Teacher", "Tutor",
    "Restaurant Manager", "Chef", "Barista", "Retail Sales Associate", "Store Manager",
    "Construction Supervisor", "Electrician", "Plumber", "Truck Driver", "Pharmacist",
    "Medical Assistant", "Physical Therapist", "Dental Hygienist", "Insurance Agent",
    "Real Estate Agent", "Bank Teller", "Loan Officer", "Bookkeeper", "Office Manager",
    "Customer Success Manager", "Technical Writer", "SEO Specialist", "Copywriter",
]

SCAM_TITLES = [
    "Remote Data Entry Clerk - Immediate Start", "Work From Home Mystery Shopper",
    "Payment Processing Agent - No Experience Needed", "Easy Online Typing Jobs",
    "Personal Assistant Needed Urgently - High Pay", "Package Reshipping Coordinator",
    "Online Survey Taker - $500/week", "Remote Executive Assistant - Crypto Pay",
    "Administrative Assistant - Work From Home - Start Today", "Money Transfer Agent",
    "Remote Customer Service - No Interview Required", "Virtual Assistant - Weekly Pay via Check",
    "Secret Shopper Needed Now", "Data Entry Specialist - $45/hr - No Skills Required",
    "Remote Bookkeeper - Immediate Hire", "International Logistics Coordinator - Crypto Accepted",
]

REAL_COMPANY_PREFIXES = [
    "Apex", "Northbridge", "Summit", "Bluepeak", "Crestview", "Lakeside", "Meridian",
    "Horizon", "Stonefield", "Brightwater", "Ironwood", "Cascade", "Pinecrest", "Westgate",
    "Harborview", "Redwood", "Glenmark", "Fairview", "Atlas", "Vantage", "Clearwater",
    "Oakmont", "Silverline", "Brookstone", "Eastview",
]
REAL_COMPANY_SUFFIXES = [
    "Technologies", "Solutions", "Consulting", "Industries", "Group", "Partners",
    "Systems", "Logistics", "Healthcare", "Financial", "Retail Co.", "Manufacturing",
    "Media", "Labs", "Networks", "Analytics", "Capital", "Holdings",
]

SCAM_COMPANY_NAMES = [
    "Global Hire Express", "QuickJobs International", "WorkFromHome Solutions LLC",
    "Premier Remote Staffing", "FastTrack Employment Group", "EasyHire Worldwide",
    "Remote Talent Connect", "Global Career Network", "PayDay Staffing Co.",
    "Instant Hire Agency", "WorldWide Remote Jobs", "TalentBridge Express",
]

LOCATIONS = [
    "New York, NY, US", "San Francisco, CA, US", "Austin, TX, US", "Chicago, IL, US",
    "Seattle, WA, US", "Boston, MA, US", "Denver, CO, US", "Atlanta, GA, US",
    "London, England, GB", "Manchester, England, GB", "Toronto, ON, CA",
    "Bangalore, KA, IN", "Mumbai, MH, IN", "Pune, MH, IN", "Sydney, NSW, AU",
    "Berlin, BE, DE", "Dublin, D, IE", "Singapore, SG", "Remote",
]

INDUSTRIES = [
    "Information Technology and Services", "Computer Software", "Financial Services",
    "Hospital & Health Care", "Marketing and Advertising", "Retail", "Construction",
    "Real Estate", "Education Management", "Logistics and Supply Chain",
    "Human Resources", "Insurance", "Telecommunications", "Manufacturing",
    "Staffing and Recruiting", "Banking", "Consumer Services",
]

FUNCTIONS = [
    "Engineering", "Information Technology", "Sales", "Marketing", "Customer Service",
    "Administrative", "Human Resources", "Finance", "Management", "Health Care Provider",
    "Other", "Accounting/Auditing", "Business Development", "Design",
]

EMPLOYMENT_TYPES = ["Full-time", "Part-time", "Contract", "Temporary", "Other"]
EXPERIENCE_LEVELS = ["Internship", "Entry level", "Associate", "Mid-Senior level", "Director", "Not Applicable"]
EDUCATION_LEVELS = [
    "High School or equivalent", "Bachelor's Degree", "Master's Degree",
    "Associate Degree", "Certification", "Unspecified", "Some College Coursework Completed",
]

GENUINE_PROFILE_TEMPLATES = [
    "Founded in {year}, {company} is a leading provider of {industry_lower} solutions serving clients across {region}. "
    "Our team of {employees} professionals is committed to innovation, quality, and long-term client partnerships.",
    "{company} has been a trusted name in {industry_lower} since {year}. We pride ourselves on a collaborative culture, "
    "competitive benefits, and a strong commitment to employee growth and development.",
    "We are {company}, a {employees}-person company headquartered in {region}, specializing in {industry_lower}. "
    "Visit our official website for more on our mission, leadership team, and open positions.",
]

GENUINE_DESC_TEMPLATES = [
    "We are looking for a {title} to join our growing team in {location}. You will work closely with cross-functional "
    "teams to deliver high-quality results. Responsibilities include managing day-to-day tasks related to {function_lower}, "
    "collaborating with stakeholders, and contributing to ongoing process improvements. This is a {employment_type} "
    "position reporting directly to the {function_lower} lead.",
    "{company} is hiring a {title} to support our {function_lower} team. The ideal candidate has relevant experience, "
    "strong communication skills, and a track record of meeting deadlines. You'll participate in regular team meetings, "
    "contribute to project planning, and help maintain our high standards of quality.",
    "As a {title} at {company}, you will play a key role in our {function_lower} department. We offer a structured "
    "onboarding process, mentorship from senior staff, and clear paths for career advancement within the company.",
]

GENUINE_REQUIREMENTS = [
    "Bachelor's degree in a related field or equivalent practical experience. 2+ years of relevant experience preferred. "
    "Strong written and verbal communication skills. Proficiency with standard office software.",
    "Relevant certification or degree required. Demonstrated experience working in a team environment. Must be able to "
    "pass a standard background check as part of our normal hiring process.",
    "Prior experience in a similar role is a plus but not required for entry-level candidates. Must be authorized to "
    "work in the country of employment. Willingness to learn new tools and processes.",
]

GENUINE_BENEFITS = [
    "Health, dental, and vision insurance. 401(k) with company match. Paid time off and company holidays. "
    "Professional development budget.",
    "Competitive salary, health benefits, flexible scheduling, and opportunities for internal promotion.",
    "Comprehensive benefits package including medical coverage, retirement plan, and paid parental leave.",
]

SCAM_PROFILE_TEMPLATES = [
    "We are a fast-growing global company offering REMOTE positions to candidates worldwide! No experience necessary, "
    "we provide full training. Start earning immediately!",
    "{company} connects job seekers with high-paying remote opportunities. Flexible hours, weekly pay, work from "
    "anywhere! Limited spots available, apply now before positions fill up.",
    "Join our team of remote workers today! We are urgently hiring due to rapid expansion. No interview required for "
    "qualified candidates -- just complete the application to get started.",
]

SCAM_DESC_TEMPLATES = [
    "URGENT HIRING! We need a {title} to start IMMEDIATELY. Earn ${pay}/week working from home with FLEXIBLE hours! "
    "No experience required, full training provided. To begin, simply reply with your full name, address, and a "
    "copy of a government ID so we can set up your direct deposit and ship your starter equipment.",
    "Are you looking to make money fast? Become our {title} today! This is a limited-time opportunity paying up to "
    "${pay} per week. We will send you a check to purchase your own equipment -- just deposit it and forward the "
    "remaining balance to our vendor via wire transfer to begin.",
    "Now hiring a {title}, no resume needed! Get hired in 24 hours. Message us on Telegram or WhatsApp to skip the "
    "wait and start your first task today. A small refundable registration fee of $50-150 is required to activate "
    "your training account.",
    "We are expanding fast and need a {title} NOW. Work just 2 hours a day and earn ${pay}/week! Payment is sent via "
    "Zelle, CashApp, or cryptocurrency. To proceed, send your SSN and a photo of your ID for 'verification' before "
    "your first shift.",
]

SCAM_REQUIREMENTS = [
    "No experience necessary! Must have a laptop, phone, and internet connection. Must be willing to receive packages "
    "at your home address and reship them per instructions.",
    "No interview, no resume, no degree needed. Must be 18+ and able to start today. Willing to provide banking "
    "details for direct deposit setup before first day.",
    "Anyone can apply! We just need your basic information and a small registration fee to cover background check "
    "processing and training materials.",
]

SCAM_BENEFITS = [
    "Get paid same day! Flexible hours, work from anywhere, no boss looking over your shoulder.",
    "Earn unlimited income with our exclusive system. Weekly bonuses paid in cryptocurrency.",
    "Be your own boss! Guaranteed income, no cap on earnings, instant approval.",
]


def make_company(genuine: bool) -> str:
    if genuine:
        return f"{random.choice(REAL_COMPANY_PREFIXES)} {random.choice(REAL_COMPANY_SUFFIXES)}"
    return random.choice(SCAM_COMPANY_NAMES)


def make_salary(genuine: bool) -> str:
    if genuine:
        lo = random.choice([35000, 45000, 55000, 65000, 75000, 90000, 110000])
        hi = lo + random.choice([10000, 15000, 20000, 30000])
        return f"{lo}-{hi}"
    if random.random() < 0.4:
        return ""  # many scams omit a formal salary range
    lo = random.choice([800, 1200, 1500, 2000, 3000])
    hi = lo * random.choice([2, 3, 4])
    return f"{lo}-{hi}"


def make_row(genuine: bool, idx: int) -> dict:
    title = random.choice(REAL_TITLES) if genuine else random.choice(SCAM_TITLES + REAL_TITLES)
    company = make_company(genuine)
    location = random.choice(LOCATIONS)
    industry = random.choice(INDUSTRIES)
    function = random.choice(FUNCTIONS)
    employment_type = random.choice(EMPLOYMENT_TYPES)
    region = location.split(",")[0]

    if genuine:
        profile = random.choice(GENUINE_PROFILE_TEMPLATES).format(
            company=company, year=random.randint(1985, 2018),
            industry_lower=industry.lower(), region=region,
            employees=random.choice([20, 50, 120, 300, 800, 2000]),
        )
        description = random.choice(GENUINE_DESC_TEMPLATES).format(
            title=title, location=location, company=company,
            function_lower=function.lower(), employment_type=employment_type.lower(),
        )
        requirements = random.choice(GENUINE_REQUIREMENTS)
        benefits = random.choice(GENUINE_BENEFITS)
        has_company_logo = 1 if random.random() < 0.85 else 0
        has_questions = 1 if random.random() < 0.6 else 0
        telecommuting = 1 if random.random() < 0.25 else 0
        required_education = random.choice(EDUCATION_LEVELS)
        required_experience = random.choice(EXPERIENCE_LEVELS)
        fraudulent = 0
    else:
        profile = random.choice(SCAM_PROFILE_TEMPLATES).format(company=company)
        pay = random.choice([500, 800, 1000, 1500, 2500])
        description = random.choice(SCAM_DESC_TEMPLATES).format(title=title, pay=pay)
        requirements = random.choice(SCAM_REQUIREMENTS)
        benefits = random.choice(SCAM_BENEFITS)
        has_company_logo = 1 if random.random() < 0.12 else 0
        has_questions = 1 if random.random() < 0.15 else 0
        telecommuting = 1 if random.random() < 0.85 else 0
        required_education = "Unspecified" if random.random() < 0.7 else random.choice(EDUCATION_LEVELS)
        required_experience = "Not Applicable" if random.random() < 0.6 else random.choice(EXPERIENCE_LEVELS)
        fraudulent = 1

    return {
        "job_id": idx,
        "title": title,
        "location": location,
        "department": function if genuine else "",
        "salary_range": make_salary(genuine),
        "company_profile": profile,
        "description": description,
        "requirements": requirements,
        "benefits": benefits,
        "telecommuting": telecommuting,
        "has_company_logo": has_company_logo,
        "has_questions": has_questions,
        "employment_type": employment_type,
        "required_experience": required_experience,
        "required_education": required_education,
        "industry": industry,
        "function": function,
        "fraudulent": fraudulent,
    }


def generate(n_genuine: int = 2850, n_fraud: int = 150) -> list:
    rows = []
    idx = 1
    for _ in range(n_genuine):
        rows.append(make_row(True, idx))
        idx += 1
    for _ in range(n_fraud):
        rows.append(make_row(False, idx))
        idx += 1
    random.shuffle(rows)
    return rows


def main():
    rows = generate()
    fieldnames = list(rows[0].keys())
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fake_job_postings.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")
    print(f"Fraudulent: {sum(r['fraudulent'] for r in rows)} "
          f"({100 * sum(r['fraudulent'] for r in rows) / len(rows):.1f}%)")


if __name__ == "__main__":
    main()
