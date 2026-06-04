export type ApplicationStatus = "draft" | "submitted" | "evaluated";

export interface Borrower {
  legal_name: string;
  industry: string;
  state: string;
  years_in_business: number;
  annual_revenue: number;
  is_us_citizen: boolean;
  has_physical_location: boolean;
  is_startup: boolean;
}

export interface Guarantor {
  name: string;
  fico: number;
  revolving_balance: number;
  unsecured_debt: number;
  homeowner: boolean;
  has_bankruptcy: boolean;
  bk_discharge_years: number | null;
  has_judgments: boolean;
  has_foreclosure: boolean;
  has_repossession: boolean;
  has_tax_lien: boolean;
  has_recent_collections: boolean;
}

export interface BusinessCredit {
  paynet_score: number | null;
  comparable_credit_pct: number;
  trade_lines_count: number;
  clean_payment_history_months: number;
}

export interface LoanRequest {
  amount: number;
  term_months: number;
  equipment_type: string;
  equipment_year: number | null;
  equipment_age_years: number | null;
  down_payment_pct: number;
  is_private_party: boolean;
}

export interface ApplicationCreate {
  borrower: Borrower;
  guarantor: Guarantor;
  business_credit: BusinessCredit;
  loan_request: LoanRequest;
}

export interface ApplicationSummary {
  id: number;
  status: ApplicationStatus;
  legal_name: string | null;
  amount: number | null;
  state: string | null;
  industry: string | null;
  created_at: string;
}

export interface ApplicationRead extends ApplicationCreate {
  id: number;
  status: ApplicationStatus;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
}

export interface RuleEvaluation {
  id: number;
  rule_id: number;
  field: string;
  op: string;
  required: unknown;
  actual: unknown;
  passed: boolean;
  hard: boolean;
  weight: number;
  message: string;
}

export interface MatchResult {
  id: number;
  lender_id: number;
  lender_name: string;
  program_id: number | null;
  program_name: string | null;
  eligible: boolean;
  fit_score: number;
  rank: number | null;
  evaluations: RuleEvaluation[];
}

export interface Rule {
  id: number;
  program_id: number;
  kind: string;
  field: string;
  op: string;
  value: unknown;
  weight: number;
  hard: boolean;
  message: string | null;
}

export interface Program {
  id: number;
  name: string;
  priority: number;
  base_rate: number | null;
  notes: string | null;
  rules: Rule[];
}

export interface Lender {
  id: number;
  slug: string;
  name: string;
  contact: string | null;
  notes: string | null;
  active: boolean;
  programs: Program[];
}
