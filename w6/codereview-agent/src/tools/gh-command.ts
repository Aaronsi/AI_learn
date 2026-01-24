/**
 * GitHub CLI Command Tool
 * Executes GitHub CLI commands for PR operations
 */

import { Tool } from "simple-agent";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

// Allowed gh commands and operations
const ALLOWED_GH_OPERATIONS = {
  pr: ["view", "diff", "list", "status", "checks"],
  issue: ["view", "list"],
  repo: ["view"],
};

/**
 * Check if gh command is safe to execute
 */
function isCommandSafe(args: string[]): { safe: boolean; error?: string } {
  if (!args || args.length === 0) {
    return { safe: false, error: "No gh command provided" };
  }

  const firstArg = args[0]?.toLowerCase();
  const secondArg = args[1]?.toLowerCase();

  // Check if command type is allowed
  if (!Object.keys(ALLOWED_GH_OPERATIONS).includes(firstArg)) {
    return {
      safe: false,
      error: `Only ${Object.keys(ALLOWED_GH_OPERATIONS).join(", ")} commands are allowed, got: ${firstArg}`,
    };
  }

  // Check if operation is read-only
  const allowedOps =
    ALLOWED_GH_OPERATIONS[firstArg as keyof typeof ALLOWED_GH_OPERATIONS];
  if (!secondArg || !allowedOps.includes(secondArg)) {
    return {
      safe: false,
      error: `Only read-only operations allowed for '${firstArg}': ${allowedOps.join(", ")}`,
    };
  }

  return { safe: true };
}

export const ghCommandTool: Tool = {
  name: "gh_command",
  description:
    "Execute read-only GitHub CLI (gh) commands for PR operations. Only supports: pr view/diff/list/status/checks, issue view/list, repo view. Requires gh CLI to be installed and authenticated.",
  parameters: {
    type: "object",
    properties: {
      args: {
        type: "array",
        items: { type: "string" },
        description:
          "Arguments to pass to gh command. Examples: ['pr', 'view', '12'], ['pr', 'diff', '12']",
      },
    },
    required: ["args"],
  },
  execute: async (args) => {
    const { args: ghArgs } = args as { args: string[] };

    // Safety check
    const safety = isCommandSafe(ghArgs);
    if (!safety.safe) {
      return { output: "", error: safety.error };
    }

    try {
      const command = `gh ${ghArgs.join(" ")}`;
      const { stdout, stderr } = await execAsync(command, {
        maxBuffer: 10 * 1024 * 1024, // 10MB buffer
        timeout: 60000, // 60 second timeout (gh can be slower)
      });

      return { output: stdout || stderr };
    } catch (error: any) {
      // Check for gh not installed
      if (error.code === "ENOENT" || error.message.includes("not found")) {
        return {
          output: "",
          error: "GitHub CLI (gh) is not installed or not in PATH. Please install it from https://cli.github.com/",
        };
      }

      // Check for authentication error
      if (error.stderr && error.stderr.includes("authenticate")) {
        return {
          output: "",
          error: "GitHub CLI is not authenticated. Please run 'gh auth login' first.",
        };
      }

      // Other gh errors
      if (error.code && error.stderr) {
        return {
          output: "",
          error: `gh command failed: ${error.stderr.trim()}`,
        };
      }

      return {
        output: "",
        error: `Failed to execute gh command: ${error.message}`,
      };
    }
  },
};

