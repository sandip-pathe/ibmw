export interface User {
  email: string;
  user_id?: string;
}

export interface GitHubRepo {
  id: number;
  name: string;
  full_name: string;
  private: boolean;
  owner: {
    login: string;
    avatar_url: string;
  };
  description: string | null;
  html_url: string;
  default_branch: string;
  language: string | null;
  updated_at: string;
}

export interface IndexingStatus {
  repo_id: number;
  full_name: string;
  status: "pending" | "indexed";
  chunks_count: number;
  last_indexed: string | null;
}

// New Interfaces for Regulation Engine
export interface RegulationDoc {
  document_id: string;
  title: string;
  regulator: "RBI" | "SEBI";
  doc_type: string;
  publish_date: string;
  status: "active" | "draft" | "archived";
  source_url?: string;
}

export interface ScrapeResult {
  new: number;
  errors: number;
  duplicates: number;
}

export interface GitHubRepo {
  id: number;
  name: string;
  full_name: string;
  private: boolean;
  owner: {
    login: string;
    avatar_url: string;
  };
  description: string | null;
  html_url: string;
  default_branch: string;
  language: string | null;
  updated_at: string;
}

export interface IndexingStatus {
  repo_id: number;
  full_name: string;
  status: "pending" | "indexed";
  chunks_count: number;
  last_indexed: string | null;
}

export interface Violation {
  violation_id: string;
  rule_id: string;
  verdict: "compliant" | "non_compliant" | "partial" | "unknown";
  severity: "critical" | "high" | "medium" | "low";
  severity_score: number;
  explanation: string;
  evidence?: string;
  remediation?: string;
  file_path: string;
  start_line: number;
  end_line: number;
  status: "pending" | "approved" | "rejected" | "ignored";
  reviewer_note?: string;
  jira_ticket_id?: string;
  created_at: string;
}

export interface ScanStatus {
  scan_id: string;
  status: "pending" | "running" | "completed" | "failed";
  total_violations: number;
  violations_found?: number;
  logs?: AgentLog[];
}

export interface AgentLog {
  agent: "PLANNER" | "NAVIGATOR" | "INVESTIGATOR" | "JUDGE" | "JIRA";
  message: string;
  timestamp: string;
  ts_epoch: number;
}
