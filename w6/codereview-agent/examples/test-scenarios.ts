/**
 * Test: Run multiple review scenarios
 */

import { runCodeReview } from "../src/index";

const scenarios = [
  {
    name: "Review uncommitted changes",
    message: "帮我 review 最近的改动",
  },
  {
    name: "Review current branch vs main",
    message: "帮我 review 当前 branch 相对于 main 分支的新代码",
  },
];

async function runTests() {
  console.log("🧪 Running Code Review Agent Tests\n");

  for (const scenario of scenarios) {
    console.log("=".repeat(70));
    console.log(`Test: ${scenario.name}`);
    console.log(`Message: ${scenario.message}`);
    console.log("=".repeat(70));

    try {
      const response = await runCodeReview(scenario.message, {
        temperature: 0.7,
        maxTokens: 4096,
      });

      console.log("\n📋 Review Result:");
      console.log(response);
      console.log("\n✅ Test passed\n");
    } catch (error) {
      console.error("\n❌ Test failed:", (error as Error).message);
      console.error((error as Error).stack);
    }

    // Add delay between tests to avoid rate limiting
    if (scenario !== scenarios[scenarios.length - 1]) {
      console.log("\n⏳ Waiting 2 seconds before next test...\n");
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  }

  console.log("\n" + "=".repeat(70));
  console.log("✨ All tests completed");
  console.log("=".repeat(70));
}

runTests().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});

