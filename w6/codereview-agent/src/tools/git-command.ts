/**
 * Git Command Tool
 * Executes git commands for code review purposes
 */

import { Tool } from "simple-agent";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

// Blocked dangerous git commands
const BLOCKED_GIT_COMMANDS = [
  "reset",
  "checkout", // Can discard changes
  "clean",
  "revert",
  "push",
  "pull",
  "merge",
  "rebase",
  "cherry-pick",
  "commit",
  "add",
  "rm",
  "mv",
  "tag",
  "stash",
  "--force",
  "-f",
];

/**
 * Check if git command is safe to execute
 */
function isCommandSafe(args: string[]): { safe: boolean; error?: string } {
  if (!args || args.length === 0) {
    return { safe: false, error: "No git command provided" };
  }

  // Check first argument (main command)
  const firstArg = args[0].toLowerCase();
  const dangerousFirstArgs = [
    "reset",
    "checkout",
    "clean",
    "revert",
    "push",
    "pull",
    "merge",
    "rebase",
    "cherry-pick",
    "commit",
    "add",
    "rm",
    "mv",
    "tag",
    "stash",
  ];

  if (dangerousFirstArgs.includes(firstArg)) {
    return {
      safe: false,
      error: `Dangerous git command blocked: '${firstArg}'. Only read-only git commands are allowed.`,
    };
  }

  // Check for dangerous flags as separate arguments
  const dangerousFlags = ["--force", "-f"];
  for (const arg of args) {
    const lowerArg = arg.toLowerCase();
    if (dangerousFlags.includes(lowerArg)) {
      return {
        safe: false,
        error: `Dangerous git flag blocked: '${arg}'. Only read-only git commands are allowed.`,
      };
    }
  }

  return { safe: true };
}

export const gitCommandTool: Tool = {
  name: "git_command",
  description:
    "Execute read-only git commands to get code changes, history, and repository information. Supports: diff, show, log, status, branch, etc. Dangerous commands (reset, checkout, push, etc.) are blocked.",
  parameters: {
    type: "object",
    properties: {
      args: {
        type: "array",
        items: { type: "string" },
        description:
          "Arguments to pass to git command. Examples: ['diff'], ['show', 'abc123'], ['diff', 'main...HEAD']",
      },
    },
    required: ["args"],
  },
  execute: async (args) => {
    const { args: gitArgs } = args as { args: string[] };

    // Safety check
    const safety = isCommandSafe(gitArgs);
    if (!safety.safe) {
      return { output: "", error: safety.error };
    }

    try {
      const command = `git ${gitArgs.join(" ")}`;
      const { stdout, stderr } = await execAsync(command, {
        maxBuffer: 10 * 1024 * 1024, // 10MB buffer for large diffs
        timeout: 30000, // 30 second timeout
      });

      // Git sometimes outputs to stderr even on success
      return { output: stdout || stderr };
    } catch (error: any) {
      // Check if it's a git error (non-zero exit code)
      if (error.code && error.stderr) {
        return {
          output: "",
          error: `Git command failed: ${error.stderr.trim()}`,
        };
      }
      return {
        output: "",
        error: `Failed to execute git command: ${error.message}`,
      };
    }
  },
};

