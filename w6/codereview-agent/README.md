# Code Review Agent

AI-powered code review agent based on the simple-agent framework.

## Features

- **Multi-scenario Reviews**: Branch diffs, commit diffs, PR reviews
- **Context-Aware**: Reads full files, not just diffs
- **Focused Feedback**: Bugs > Structure > Performance
- **Safe by Design**: Read-only git/gh commands, sandboxed file access

## Installation

```bash
cd w6/codereview-agent
npm install
npm run build
```

## Usage

### CLI

```bash
# Review uncommitted changes
npm run cli

# Review current branch
npm run cli "帮我 review 当前 branch 新代码"

# Review specific commit
npm run cli "帮我 review commit abc123 之后的代码"

# Review PR (requires gh CLI)
npm run cli "帮我 review pull request 12 的代码"
```

### Programmatic

```typescript
import { runCodeReview } from "codereview-agent";

const response = await runCodeReview("帮我 review 最近的改动");
console.log(response);
```

### Streaming

```typescript
import { streamCodeReview } from "codereview-agent";

for await (const chunk of streamCodeReview("帮我 review 当前 branch 新代码")) {
  process.stdout.write(chunk);
}
```

## Environment Variables

```bash
# DeepSeek API (default)
export DEEPSEEK_API_KEY=your-api-key

# Or OpenAI
export OPENAI_API_KEY=your-api-key
export DEEPSEEK_BASE_URL=https://api.openai.com
```

## Architecture

```
┌─────────────────────────────────────────┐
│         Code Review Agent               │
├─────────────────────────────────────────┤
│  System Prompt (prompts/system.md)     │
│  - Review workflow rules                │
│  - Analysis standards                   │
│  - Output format                        │
├─────────────────────────────────────────┤
│  Tools (src/tools/)                     │
│  - read_file: Read source files        │
│  - write_file: Write reports           │
│  - git_command: Get diffs/history      │
│  - gh_command: PR operations           │
├─────────────────────────────────────────┤
│         Simple-Agent Core               │
│  - Agent loop                           │
│  - LLM client                           │
│  - Tool executor                        │
└─────────────────────────────────────────┘
```

## Design Principles

1. **Thin Wrapper**: Agent only provides tools and safety checks
2. **LLM-Driven**: All business logic in system prompt
3. **No Intent Parsing**: Pass user messages directly to LLM

## Safety

- Read-only git commands (no reset/push/merge)
- Read-only gh commands (view/diff/list only)
- Sandboxed file access (no .. traversal, no sensitive files)

