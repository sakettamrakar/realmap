import axios from "axios";
import type { AIScoreResponse, HealthCheckResponse } from "../types/ai";

// Use the same base URL as the robust client for now, or a separate one if deployed differently.
// Using relative path assuming proxy or same origin for simplicity in dev.
// In production this might point to a different microservice URL.
const AI_API_BASE = (import.meta.env.VITE_AI_API_URL as string) || "http://localhost:8001";

export const aiClient = axios.create({
    baseURL: AI_API_BASE,
    timeout: 60000, // 60s timeout for LLM generation
    headers: {
        "Content-Type": "application/json",
    },
});

export async function getProjectScore(projectId: number): Promise<AIScoreResponse> {
    try {
        // Try fetching existing score first (stub logic in backend implies this endpoint handles generation too if posted)
        // But per runbook: POST filters generation. GET retrieves.
        // Let's implement the "Get or Generate" pattern here or in the component.
        // For this MVP, we will call POST to ensure we get a result (it returns existing or new)
        const { data } = await aiClient.post<AIScoreResponse>(`/ai/score/project/${projectId}`);
        return data;
    } catch (error) {
        console.error("AI Service Error", error);
        throw error;
    }
}

export async function checkAIHealth(): Promise<boolean> {
    try {
        const { data } = await aiClient.get<HealthCheckResponse>("/ai/health");
        return data.status === "ok";
    } catch (error) {
        return false;
    }
}
