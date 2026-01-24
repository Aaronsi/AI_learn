"use strict";
/**
 * Write File Tool
 * Writes content to a file in the current working directory
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.writeFileTool = void 0;
const fs = __importStar(require("fs/promises"));
const path = __importStar(require("path"));
/**
 * Validate file path for security
 */
function validatePath(filePath) {
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
exports.writeFileTool = {
    name: "write_file",
    description: "Write content to a file in the current working directory. Use this to output review reports or save analysis results.",
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
        const { path: filePath, content } = args;
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
        }
        catch (error) {
            const err = error;
            if (err.code === "EACCES") {
                return { output: "", error: `Permission denied: ${filePath}` };
            }
            return { output: "", error: `Failed to write file: ${err.message}` };
        }
    },
};
//# sourceMappingURL=write-file.js.map