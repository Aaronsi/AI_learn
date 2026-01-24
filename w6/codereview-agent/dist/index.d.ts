/**
 * Code Review Agent
 * Main entry point for the code review agent
 */
import { SimpleAgent } from "simple-agent";
export interface CodeReviewAgentConfig {
    model?: string;
    apiKey?: string;
    baseURL?: string;
    temperature?: number;
    maxTokens?: number;
    maxSteps?: number;
}
/**
 * Create a code review agent instance
 */
export declare function createCodeReviewAgent(config?: CodeReviewAgentConfig): SimpleAgent;
/**
 * Run code review with a user message
 */
export declare function runCodeReview(userMessage: string, config?: CodeReviewAgentConfig): Promise<string>;
/**
 * Run code review with streaming output
 */
export declare function streamCodeReview(userMessage: string, config?: CodeReviewAgentConfig): AsyncGenerator<string>;
export * from "./tools";
//# sourceMappingURL=index.d.ts.map