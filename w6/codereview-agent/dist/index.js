"use strict";
/**
 * Code Review Agent
 * Main entry point for the code review agent
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __exportStar = (this && this.__exportStar) || function(m, exports) {
    for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(exports, p)) __createBinding(exports, m, p);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.createCodeReviewAgent = createCodeReviewAgent;
exports.runCodeReview = runCodeReview;
exports.streamCodeReview = streamCodeReview;
const simple_agent_1 = require("simple-agent");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const tools_1 = require("./tools");
// Load system prompt
const systemPromptPath = path.join(__dirname, "../prompts/system.md");
let systemPrompt;
try {
    systemPrompt = fs.readFileSync(systemPromptPath, "utf-8");
}
catch (error) {
    // Try alternate paths (for different build configurations)
    const alternatePath = path.join(process.cwd(), "prompts/system.md");
    try {
        systemPrompt = fs.readFileSync(alternatePath, "utf-8");
    }
    catch {
        throw new Error(`Failed to load system prompt from ${systemPromptPath} or ${alternatePath}. ` +
            `Please ensure prompts/system.md exists.`);
    }
}
/**
 * Create a code review agent instance
 */
function createCodeReviewAgent(config = {}) {
    const agent = new simple_agent_1.SimpleAgent({
        model: config.model || "deepseek-chat",
        systemPrompt,
        temperature: config.temperature ?? 0.7,
        maxTokens: config.maxTokens ?? 4096,
        maxSteps: config.maxSteps ?? 50,
        llmConfig: {
            apiKey: config.apiKey,
            baseURL: config.baseURL,
        },
    });
    // Register tools
    agent.addTools([tools_1.readFileTool, tools_1.writeFileTool, tools_1.gitCommandTool, tools_1.ghCommandTool]);
    return agent;
}
/**
 * Run code review with a user message
 */
async function runCodeReview(userMessage, config = {}) {
    const agent = createCodeReviewAgent(config);
    const session = agent.createSession();
    try {
        const response = await agent.run(session.id, userMessage);
        return response;
    }
    catch (error) {
        throw new Error(`Code review failed: ${error.message}`);
    }
}
/**
 * Run code review with streaming output
 */
async function* streamCodeReview(userMessage, config = {}) {
    const agent = createCodeReviewAgent(config);
    const session = agent.createSession();
    try {
        for await (const event of agent.stream(session.id, userMessage)) {
            if (event.type === "text") {
                yield event.text;
            }
            else if (event.type === "tool_call") {
                // Optionally show tool calls
                // yield `\n[Calling ${event.name}...]\n`;
            }
            else if (event.type === "error") {
                throw event.error;
            }
        }
    }
    catch (error) {
        throw new Error(`Code review failed: ${error.message}`);
    }
}
// Export tools for advanced usage
__exportStar(require("./tools"), exports);
//# sourceMappingURL=index.js.map