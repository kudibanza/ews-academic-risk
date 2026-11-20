export interface StudentSummary {
  student_id: number;
  presentation: string;
  risk_score: number;
  flagged: boolean;
}

export interface Factor {
  feature: string;
  shap_value: number;
  feature_value: number | string | null;
}

export interface RiskCard {
  student_id: number;
  presentation: string;
  window: string;
  risk_score: number;
  threshold_applied: number;
  flagged: boolean;
  top_positive_factors: Factor[];
  top_negative_factors: Factor[];
  other_factors_sum: number;
  base_value: number;
}

export interface SCSQuestion {
  id: number;
  text: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface AdminUser {
  id: number;
  username: string;
  role: "admin" | "advisor";
  active: boolean;
}

export interface RiskBin {
  bin_start: number;
  bin_end: number;
  count: number;
}

export interface TopFeature {
  feature: string;
  mean_abs_shap: number;
}

export interface WindowStats {
  window: string;
  n_students: number;
  n_flagged: number;
  flagged_pct: number;
  risk_bins: RiskBin[];
  top_features: TopFeature[];
}

