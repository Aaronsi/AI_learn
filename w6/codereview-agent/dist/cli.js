#!/usr/bin/env node
"use strict";
/**
 * Code Review Agent CLI
 * Command-line interface for running code reviews
 */
Object.defineProperty(exports, "__esModule", { value: true });
const index_1 = require("./index");
async function main() {
    const args = process.argv.slice(2);
    // Get user message from arguments or use default
    const userMessage = args.length > 0 ? args.join(" ") : "帮我 review 最近的改动";
    console.log("🔍 Code Review Agent");
    console.log("━".repeat(50));
    console.log(`Request: ${userMessage}\n`);
    try {
        // Check for streaming flag
        const useStreaming = process.env.STREAM === "true";
        if (useStreaming) {
            // Streaming mode
            for await (const chunk of (0, index_1.streamCodeReview)(userMessage)) {
                process.stdout.write(chunk);
            }
            console.log(); // Final newline
        }
        else {
            // Non-streaming mode
            const response = await (0, index_1.runCodeReview)(userMessage);
            console.log(response);
        }
        console.log("\n" + "━".repeat(50));
        console.log("✅ Review completed");
    }
    catch (error) {
        console.error("\n" + "━".repeat(50));
        console.error("❌ Error:", error.message);
        process.exit(1);
    }
}
main();
//# sourceMappingURL=cli.js.map