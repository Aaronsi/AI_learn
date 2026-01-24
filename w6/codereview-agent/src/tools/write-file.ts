/**
 * Write File Tool
 * Writes content to a file in the current working directory
 */

import { Tool } from "simple-agent";
import * as fs from "fs/promises";
import * as path from "path";

/**
 * Validate file path for security
 */
function validatePath(filePath: string): { valid: boolean; error?: string } {
  // 1. Prohibit absolute paths
  if (path.isAbsolute(filePath)) {
    return { valid: false, error: "Absolute paths are not allowed" };
  }

  // 2. Prohibit path traversal
  if (filePath.includes("..")) {
    return { valid: false, error: "Path traversal is not allowed" };
  }

  // 3. Prohibit writing to sensitive locations
  const sensitive = [".env", ".git/", "id_rsa", "secrets", ".ssh/"];
  if (sensitive.some((s) => filePath.includes(s))) {
    return {
      valid: false,
      error: `Writing to sensitive locations (${sensitive.join(", ")}) is not allowed`,
    };
  }

  return { valid: true };
}

export const writeFileTool: Tool = {
  name: "write_file",
  description:
    "Write content to a file in the current working directory. Use this to output review reports or save analysis results.",
  parameters: {
    type: "object",
    properties: {
      path: {
        type: "string",
        description: "Relative path to the file to write (e.g., 'review-report.md')",
      },
      content: {
        type: "string",
        description: "Content to write to the file",
      },
    },
    required: ["path", "content"],
  },
  execute: async (args) => {
    const { path: filePath, content } = args as {
      path: string;
      content: string;
    };

    // Validate path
    const validation = validatePath(filePath);
    if (!validation.valid) {
      return { output: "", error: validation.error };
    }

    try {
      // Ensure directory exists
      const dir = path.dirname(filePath);
      if (dir !== ".") {
        await fs.mkdir(dir, { recursive: true });
      }

      await fs.writeFile(filePath, content, "utf-8");
      return { output: `Successfully wrote to ${filePath}` };
    } catch (error) {
      const err = error as NodeJS.ErrnoException;
      if (err.code === "EACCES") {
        return { output: "", error: `Permission denied: ${filePath}` };
      }
      return { output: "", error: `Failed to write file: ${err.message}` };
    }
  },
};

