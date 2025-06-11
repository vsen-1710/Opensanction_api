from typing import List
from dataclasses import dataclass

@dataclass
class CrimeDomain:
    """Model representing a crime domain with its attributes"""
    name: str
    code: str
    category: str
    priority: str

@dataclass
class CrimeStage:
    """Model representing a crime stage with its attributes"""
    name: str
    code: str
    description: str
    stage: str

# List of crime domains
CRIME_DOMAINS: List[CrimeDomain] = [
    CrimeDomain("Firm Specific Black List", "BLK", "Regulatory Risks", "P0"),
    CrimeDomain("Bribery, Graft, Kickbacks", "BRB", "Fraud and Corruption", "P0"),
    CrimeDomain("Business Crimes", "BUS", "Fraud and Corruption", "P0"),
    CrimeDomain("Denied Entity", "DEN", "Regulatory Risks", "P0"),
    CrimeDomain("Foreign Agent Registration Act", "FAR", "Fraud and Corruption", "P0"),
    CrimeDomain("Former OFAC List", "FOF", "Regulatory Risks", "P0"),
    CrimeDomain("Former Sanctions", "FOS", "Regulatory Risks", "P0"),
    CrimeDomain("Fraud, Scams, Swindles", "FRD", "Fraud and Corruption", "P0"),
    CrimeDomain("Hate crimes & Hate groups", "HTE", "Social and Ethical Risks", "P0"),
    CrimeDomain("Iran Connect", "IRC", "Regulatory Risks", "P0"),
    CrimeDomain("Money Laundering", "MLA", "Fraud and Corruption", "P0"),
    CrimeDomain("Organized Crime", "ORG", "Fraud and Corruption", "P0"),
    CrimeDomain("Person Political", "PEP", "Regulatory Risks", "P0"),
    CrimeDomain("Regulatory Action", "REG", "Regulatory Risks", "P0"),
    CrimeDomain("SEC Violations", "SEC", "Regulatory Risks", "P0"),
    CrimeDomain("Sanctions Connect", "SNX", "Regulatory Risks", "P0"),
    CrimeDomain("Terrorist Related", "TER", "Social and Ethical Risks", "P0"),
    CrimeDomain("Watch List", "WLT", "Regulatory Risks", "P0"),
    CrimeDomain("Environmental Crimes", "ENV", "Social and Ethical Risks", "P0"),
    CrimeDomain("Human Rights, Genocide, War Crimes", "HUM", "Social and Ethical Risks", "P0"),
    CrimeDomain("Cyber Crime", "CYB", "Cyber and Technology Risks", "P1"),
    CrimeDomain("Trafficking or Distribution of Drug", "DTF", "Fraud and Corruption", "P1"),
    CrimeDomain("Fugitive, Escape", "FUG", "Social and Ethical Risks", "P1"),
    CrimeDomain("Identity Theft, Impersonation", "IMP", "Fraud and Corruption", "P1"),
    CrimeDomain("Kidnapping, Abduction", "KID", "Social and Ethical Risks", "P1"),
    CrimeDomain("Murder, Manslaughter", "MUR", "Social and Ethical Risks", "P1"),
    CrimeDomain("Obscenity Related, Child Pornography", "OBS", "Social and Ethical Risks", "P1"),
    CrimeDomain("Perjury, Obstruction of Justice", "PRJ", "Fraud and Corruption", "P1"),
    CrimeDomain("Sex Offenses", "SEX", "Social and Ethical Risks", "P1"),
    CrimeDomain("Smuggling", "SMG", "Fraud and Corruption", "P1"),
    CrimeDomain("People Trafficking, Organ Trafficking", "TRF", "Social and Ethical Risks", "P1"),
    CrimeDomain("Tax Related Offenses", "TAX", "Fraud and Corruption", "P1"),
    CrimeDomain("Copyright Infringement", "CPR", "Cyber and Technology Risks", "P1"),
    CrimeDomain("Data privacy and protection", "DPP", "Cyber and Technology Risks", "P1"),
    CrimeDomain("Conspiracy", "CON", "Fraud and Corruption", "P2"),
    CrimeDomain("Possession of Drugs or Paraphernalia", "DPS", "Fraud and Corruption", "P2"),
    CrimeDomain("Forfeiture", "FOR", "Fraud and Corruption", "P2"),
    CrimeDomain("Possession or Sale of Guns", "IGN", "Social and Ethical Risks", "P2"),
    CrimeDomain("Possession of Stolen Property", "PSP", "Fraud and Corruption", "P2"),
    CrimeDomain("Robbery", "ROB", "Social and Ethical Risks", "P2"),
    CrimeDomain("Theft", "TFT", "Fraud and Corruption", "P2"),
    CrimeDomain("Real Estate Actions", "RES", "Fraud and Corruption", "P2"),
    CrimeDomain("Loan Sharking, Usury", "LNS", "Fraud and Corruption", "P2"),
    CrimeDomain("Mortgage Related", "MOR", "Fraud and Corruption", "P2"),
    CrimeDomain("Money Services Business", "MSB", "Fraud and Corruption", "P2"),
    CrimeDomain("Legal Marijuana Dispensaries", "LMD", "Regulatory Risks", "P2"),
    CrimeDomain("Illegal Gambling", "GAM", "Fraud and Corruption", "P2"),
    CrimeDomain("Counterfeiting, Forgery", "CFT", "Fraud and Corruption", "P2"),
    CrimeDomain("Abuse", "ABU", "Social and Ethical Risks", "P3"),
    CrimeDomain("Illegal Prostitution", "IPR", "Social and Ethical Risks", "P3"),
    CrimeDomain("Misconduct", "MIS", "Fraud and Corruption", "P3"),
    CrimeDomain("Nonspecific Crimes", "NSC", "Regulatory Risks", "P3"),
    CrimeDomain("Assault, Battery", "AST", "Social and Ethical Risks", "P3"),
    CrimeDomain("Burglary", "BUR", "Social and Ethical Risks", "P3"),
    CrimeDomain("Arson", "ARS", "Social and Ethical Risks", "P3"),
    CrimeDomain("Virtual Currency", "VCY", "Cyber and Technology Risks", "P3"),
    CrimeDomain("Spying", "SPY", "Social and Ethical Risks", "P3"),
]

# List of crime stages
CRIME_STAGES: List[CrimeStage] = [
    CrimeStage("Accuse", "ACC", "Stage 1: Pre-Investigation and Allegation", "Stage 1"),
    CrimeStage("Allege", "ALL", "Stage 1: Pre-Investigation and Allegation", "Stage 1"),
    CrimeStage("Conspire", "CSP", "Stage 1: Pre-Investigation and Allegation", "Stage 1"),
    CrimeStage("Probe", "PRB", "Stage 1: Pre-Investigation and Allegation", "Stage 1"),
    CrimeStage("Suspected", "SPT", "Stage 1: Pre-Investigation and Allegation", "Stage 1"),
    CrimeStage("Arraign", "ARN", "Stage 2: Investigation and Legal Proceedings", "Stage 1"),
    CrimeStage("Arrest", "ART", "Stage 2: Investigation and Legal Proceedings", "Stage 1"),
    CrimeStage("Audit", "ADT", "Stage 2: Investigation and Legal Proceedings", "Stage 1"),
    CrimeStage("Charged", "CHG", "Stage 2: Investigation and Legal Proceedings", "Stage 1"),
    CrimeStage("Complaint Filed", "CMP", "Stage 2: Investigation and Legal Proceedings", "Stage 2"),
    CrimeStage("Indict, Indictment", "IND", "Stage 2: Investigation and Legal Proceedings", "Stage 2"),
    CrimeStage("Seizure", "SEZ", "Stage 2: Investigation and Legal Proceedings", "Stage 2"),
    CrimeStage("Lien", "LIN", "Stage 2: Investigation and Legal Proceedings", "Stage 2"),
    CrimeStage("Wanted", "WTD", "Stage 2: Investigation and Legal Proceedings", "Stage 2"),
    CrimeStage("Appeal", "APL", "Stage 3: Resolution and Judgments", "Stage 2"),
    CrimeStage("Confession", "CNF", "Stage 3: Resolution and Judgments", "Stage 2"),
    CrimeStage("Plea", "PLE", "Stage 3: Resolution and Judgments", "Stage 2"),
    CrimeStage("Settlement or Suit", "SET", "Stage 3: Resolution and Judgments", "Stage 2"),
    CrimeStage("Trial", "TRL", "Stage 3: Resolution and Judgments", "Stage 2"),
    CrimeStage("Acquit, Not Guilty", "ACQ", "Stage 3: Resolution and Judgments", "Stage 2"),
    CrimeStage("Convict, Conviction", "CVT", "Stage 3: Resolution and Judgments", "Stage 3"),
    CrimeStage("Deported", "DEP", "Stage 3: Resolution and Judgments", "Stage 3"),
    CrimeStage("Dismissed", "DMS", "Stage 3: Resolution and Judgments", "Stage 3"),
    CrimeStage("Expelled", "EXP", "Stage 3: Resolution and Judgments", "Stage 3"),
    CrimeStage("Fine < $10,000", "FIL", "Stage 3: Resolution and Judgments", "Stage 3"),
    CrimeStage("Fine > $10,000", "FIM", "Stage 3: Resolution and Judgments", "Stage 3"),
    CrimeStage("Served Jail Time", "SJT", "Stage 3: Resolution and Judgments", "Stage 3"),
    CrimeStage("Disciplinary, Regulatory Action", "ACT", "Stage 4: Administrative and Regulatory Actions", "Stage 3"),
    CrimeStage("Arbitration", "ARB", "Stage 4: Administrative and Regulatory Actions", "Stage 3"),
    CrimeStage("Associated, Seen with", "ASC", "Stage 4: Administrative and Regulatory Actions", "Stage 3"),
    CrimeStage("Censure", "CEN", "Stage 4: Administrative and Regulatory Actions", "Stage 3"),
    CrimeStage("Government Official", "GOV", "Stage 4: Administrative and Regulatory Actions", "Stage 3"),
    CrimeStage("Revoked Registration", "RVK", "Stage 4: Administrative and Regulatory Actions", "Stage 3"),
    CrimeStage("Sanction", "SAN", "Stage 4: Administrative and Regulatory Actions", "Stage 3"),
    CrimeStage("Suspended", "SPD", "Stage 4: Administrative and Regulatory Actions", "Stage 3"),
] 