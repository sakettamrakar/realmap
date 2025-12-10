export interface AIScoreResponse {
    score_id: number;
    project_id: number;
    score_value: number;
    confidence: number;
    explanation: string;
    model_name: string;
    created_at: string;
    risks?: string[];
    strengths?: string[];
}

export interface HealthCheckResponse {
    status: string;
    model_loaded: boolean;
    version: string;
}
