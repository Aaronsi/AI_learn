/**
 * Read File Tool
 * Reads the contents of a file in the current working directory
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

  // 3. Prohibit access to sensitive files
  const sensitive = [".env", ".git/config", "id_rsa", "secrets", ".ssh"];
  if (sensitive.some((s) => filePath.includes(s))) {
    return {
      valid: false,
      error: `Access to sensitive files (${sensitive.join(", ")}) is not allowed`,
    };
  }

  return { valid: true };
}

export const readFileTool: Tool = {
  name: "read_file",
  description:
    "Read the contents of a file in the current working directory. Use this to understand code context, check convention files, or read any source file.",
  parameters: {
    type: "object",
    properties: {
      path: {
        type: "string",
        description: "Relative path to the file to read (e.g., 'src/utils/auth.ts', 'CONVENTIONS.md')",
      },
    },
    required: ["path"],
  },
  execute: async (args) => {
    const { path: filePath } = args as { path: string };

    // Validate path
    const validation = validatePath(filePath);
    if (!validation.valid) {
      return { output: "", error: validation.error };
    }

    try {
      const content = await fs.readFile(filePath, "utf-8");
      return { output: content };
    } catch (error) {
      const err = error as NodeJS.ErrnoException;
      if (err.code === "ENOENT") {
        return { output: "", error: `File not found: ${filePath}` };
      } else if (err.code === "EACCES") {
        return { output: "", error: `Permission denied: ${filePath}` };
      }
      return { output: "", error: `Failed to read file: ${err.message}` };
    }
  },
};

