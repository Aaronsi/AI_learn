/**
 * Example: Review branch changes
 * Demonstrates using the code review agent programmatically
 */

import { createCodeReviewAgent } from "../src/index";

async function main() {
  console.log("🔍 Code Review Agent - Branch Review Example\n");

  // Create agent
  const agent = createCodeReviewAgent({
    model: "deepseek-chat",
    temperature: 0.7,
  });

  // Create session
  const session = agent.createSession();

  // Example scenarios
  const scenarios = [
    "帮我 review 当前 branch 新代码",
    // "帮我 review commit 13bad5 之后的代码",
    // "帮我 review 最近的改动",
  ];

  for (const scenario of scenarios) {
    console.log(`\n${"=".repeat(60)}`);
    console.log(`Scenario: ${scenario}`);
    console.log("=".repeat(60));

    try {
      const response = await agent.run(session.id, scenario);
      console.log(response);
    } catch (error) {
      console.error("Error:", (error as Error).message);
    }
  }
}

main().catch(console.error);

