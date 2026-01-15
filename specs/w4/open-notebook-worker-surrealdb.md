# Open Notebook: SurrealDB 与 Worker 交互机制详解

## 1. 概述

Open Notebook 采用基于 **surreal-commands** 库的后台任务处理架构，实现了 SurrealDB 与 Worker 之间的高效协作。这种设计将耗时操作（如文档处理、向量化、播客生成）从 HTTP 请求周期中解耦，避免连接池耗尽，提供更好的用户体验。

### 1.1 核心组件

| 组件 | 职责 |
|------|------|
| **SurrealDB** | 命令队列存储、状态持久化、业务数据存储 |
| **surreal-commands** | 命令定义、注册、提交、执行、重试机制 |
| **Worker Pool** | 后台命令执行、并发控制 |
| **API Layer** | 命令提交入口、状态查询接口 |

### 1.2 设计理念

```
关键原则：
1. 异步优先 - 长时间运行的操作不阻塞用户界面
2. 可靠性 - 通过 SurrealDB 持久化确保任务不丢失
3. 可观测性 - 命令状态可查询、可追踪
4. 弹性 - 自动重试处理瞬态故障
```

---

## 2. 系统架构

### 2.1 整体架构图

```mermaid
graph TB
    subgraph "API Layer"
        API[FastAPI Endpoints]
        CS[CommandService]
    end

    subgraph "surreal-commands Library"
        REG[Command Registry]
        SUB[submit_command]
        EXEC[execute_command_sync]
        STATUS[get_command_status]
    end

    subgraph "SurrealDB"
        CMD_TABLE[(command table)]
        BIZ_DATA[(业务数据表<br/>source, note, etc.)]
    end

    subgraph "Worker Pool"
        W1[Worker 1]
        W2[Worker 2]
        WN[Worker N]
    end

    subgraph "Command Handlers"
        PC[process_source]
        VC[vectorize_source]
        EC[embed_chunk]
        GP[generate_podcast]
        RE[rebuild_embeddings]
    end

    API --> CS
    CS --> SUB
    CS --> STATUS
    SUB --> REG
    SUB --> CMD_TABLE
    STATUS --> CMD_TABLE

    CMD_TABLE --> W1
    CMD_TABLE --> W2
    CMD_TABLE --> WN

    W1 --> PC
    W1 --> VC
    W2 --> EC
    WN --> GP
    WN --> RE

    PC --> BIZ_DATA
    VC --> BIZ_DATA
    EC --> BIZ_DATA
    GP --> BIZ_DATA
    RE --> BIZ_DATA
```

### 2.2 命令流转时序图

```mermaid
sequenceDiagram
    participant Client as Frontend
    participant API as FastAPI
    participant CS as CommandService
    participant SC as surreal-commands
    participant DB as SurrealDB
    participant WP as Worker Pool
    participant CH as Command Handler

    rect rgb(240, 248, 255)
        Note over Client,DB: 阶段1: 命令提交
        Client->>API: POST /api/sources (异步模式)
        API->>CS: submit_command_job()
        CS->>SC: submit_command(app, cmd, args)
        SC->>DB: INSERT INTO command
        DB-->>SC: command_id
        SC-->>CS: command_id
        CS-->>API: command_id
        API-->>Client: 202 Accepted + command_id
    end

    rect rgb(255, 248, 240)
        Note over DB,CH: 阶段2: 后台执行
        WP->>DB: 轮询 pending commands
        DB-->>WP: command record
        WP->>DB: UPDATE status = 'running'
        WP->>CH: 执行 command handler
        CH->>DB: 业务数据操作
        CH-->>WP: result
        WP->>DB: UPDATE status = 'completed' + result
    end

    rect rgb(240, 255, 240)
        Note over Client,DB: 阶段3: 状态查询
        Client->>API: GET /api/commands/jobs/{id}
        API->>SC: get_command_status(id)
        SC->>DB: SELECT FROM command
        DB-->>SC: command record
        SC-->>API: status + result
        API-->>Client: CommandJobStatusResponse
    end
```

---

## 3. 核心机制详解

### 3.1 命令注册与定义

命令通过 `@command` 装饰器定义和注册：

```mermaid
graph LR
    subgraph "Command Definition"
        DEC["@command装饰器"]
        INP[CommandInput]
        OUT[CommandOutput]
        FN[Async Handler Function]
    end

    subgraph "Registration"
        REG[Global Registry]
        APP["app='open_notebook'"]
    end

    DEC --> REG
    INP --> FN
    FN --> OUT
    APP --> REG
```

**命令定义示例**：

```python
from surreal_commands import CommandInput, CommandOutput, command

class SourceProcessingInput(CommandInput):
    source_id: str
    content_state: Dict[str, Any]
    notebook_ids: List[str]
    transformations: List[str]
    embed: bool

class SourceProcessingOutput(CommandOutput):
    success: bool
    source_id: str
    embedded_chunks: int
    insights_created: int
    processing_time: float
    error_message: Optional[str]

@command(
    "process_source",           # 命令名称
    app="open_notebook",        # 应用标识
    retry={                     # 重试配置
        "max_attempts": 5,
        "wait_strategy": "exponential_jitter",
        "wait_min": 1,
        "wait_max": 30,
        "retry_on": [RuntimeError],
    },
)
async def process_source_command(
    input_data: SourceProcessingInput,
) -> SourceProcessingOutput:
    # 命令处理逻辑
    ...
```

### 3.2 命令提交流程

```mermaid
flowchart TD
    A[API 接收请求] --> B{处理模式?}
    B -->|async_processing=true| C[异步路径]
    B -->|async_processing=false| D[同步路径]

    C --> C1[创建 Source 记录]
    C1 --> C2[构建 CommandInput]
    C2 --> C3[submit_command]
    C3 --> C4[写入 command 表]
    C4 --> C5[更新 Source.command 字段]
    C5 --> C6[返回 202 Accepted]

    D --> D1[创建 Source 记录]
    D1 --> D2[构建 CommandInput]
    D2 --> D3[execute_command_sync]
    D3 --> D4[同步等待执行完成]
    D4 --> D5[返回完整结果]
```

**异步提交代码示例**：

```python
# api/routers/sources.py
from surreal_commands import submit_command
from api.command_service import CommandService

# 提交异步命令
command_id = await CommandService.submit_command_job(
    "open_notebook",      # app name
    "process_source",     # command name
    command_input.model_dump(),
)

# 更新 Source 记录关联 command
source.command = ensure_record_id(command_id)
await source.save()
```

### 3.3 SurrealDB command 表结构

```mermaid
erDiagram
    command {
        string id PK "command:ulid"
        string app "open_notebook"
        string name "process_source"
        json input "命令输入参数"
        string status "new|running|completed|failed"
        json result "执行结果"
        string error_message "错误信息"
        datetime created "创建时间"
        datetime updated "更新时间"
        json execution_context "执行上下文"
    }

    source {
        string id PK
        record command FK "关联的处理命令"
        string title
        text full_text
    }

    podcast_episode {
        string id PK
        record command FK "关联的生成命令"
        string name
        string audio_file
    }

    command ||--o| source : processes
    command ||--o| podcast_episode : generates
```

### 3.4 Worker 轮询与执行机制

```mermaid
flowchart TD
    subgraph "Worker Pool"
        START[Worker 启动] --> POLL[轮询 command 表]
        POLL --> CHECK{有待处理命令?}
        CHECK -->|No| WAIT[等待间隔]
        WAIT --> POLL

        CHECK -->|Yes| CLAIM[认领命令<br/>UPDATE status='running']
        CLAIM --> LOAD[加载 Command Handler]
        LOAD --> EXEC[执行 Handler]

        EXEC --> RESULT{执行结果?}
        RESULT -->|Success| SUCCESS[UPDATE status='completed'<br/>保存 result]
        RESULT -->|Transient Error| RETRY{重试次数?}
        RESULT -->|Permanent Error| FAIL[UPDATE status='failed'<br/>保存 error_message]

        RETRY -->|< max_attempts| BACKOFF[等待退避时间]
        RETRY -->|>= max_attempts| FAIL
        BACKOFF --> EXEC

        SUCCESS --> POLL
        FAIL --> POLL
    end

    subgraph "SurrealDB"
        CMD[(command table)]
    end

    POLL <--> CMD
    CLAIM --> CMD
    SUCCESS --> CMD
    FAIL --> CMD
```

---

## 4. 重试机制

### 4.1 重试策略类型

```mermaid
graph LR
    subgraph "Retry Strategies"
        EJ[Exponential Jitter<br/>1s→~2s→~4s→~8s]
        EX[Exponential<br/>1s→2s→4s→8s]
        FX[Fixed<br/>2s→2s→2s→2s]
        RD[Random<br/>随机 min~max]
    end

    subgraph "Use Cases"
        DB[数据库事务冲突]
        API[API 限流]
        NET[网络问题]
        QK[快速恢复]
    end

    EJ --> DB
    EX --> API
    RD --> NET
    FX --> QK
```

### 4.2 可重试与不可重试错误

```mermaid
graph TB
    subgraph "Transient Errors (可重试)"
        TE1[RuntimeError<br/>SurrealDB 事务冲突]
        TE2[ConnectionError<br/>网络连接失败]
        TE3[TimeoutError<br/>请求超时]
    end

    subgraph "Permanent Errors (不可重试)"
        PE1[ValueError<br/>无效输入]
        PE2[AuthenticationError<br/>认证失败]
        PE3[ConfigurationError<br/>配置错误]
    end

    subgraph "Retry Mechanism"
        RM[重试机制]
    end

    TE1 -->|Re-raise| RM
    TE2 -->|Re-raise| RM
    TE3 -->|Re-raise| RM

    PE1 -->|Catch & Return| FAIL[返回失败结果]
    PE2 -->|Catch & Return| FAIL
    PE3 -->|Catch & Return| FAIL

    RM -->|Wait + Retry| EXEC[重新执行]
    RM -->|Max Attempts| FAIL
```

### 4.3 重试配置示例

```python
# 高并发数据库操作 - 使用 exponential_jitter
@command(
    "embed_chunk",
    app="open_notebook",
    retry={
        "max_attempts": 5,
        "wait_strategy": "exponential_jitter",
        "wait_min": 1,
        "wait_max": 30,
        "retry_on": [RuntimeError, ConnectionError, TimeoutError],
    },
)
async def embed_chunk_command(input_data):
    try:
        # 执行嵌入操作
        ...
    except RuntimeError:
        # 重新抛出以触发重试
        raise
    except ValueError as e:
        # 永久错误，直接返回失败
        return EmbedChunkOutput(success=False, error_message=str(e))

# 编排命令 - 禁用重试，快速失败
@command("vectorize_source", app="open_notebook", retry=None)
async def vectorize_source_command(input_data):
    # 子任务有自己的重试逻辑
    ...
```

---

## 5. 命令类型与数据流

### 5.1 已注册的命令

| 命令名称 | 用途 | 重试策略 |
|----------|------|----------|
| `process_source` | 处理源内容（提取文本、生成洞察） | 5次，exponential_jitter |
| `vectorize_source` | 编排向量化任务 | 禁用（快速失败） |
| `embed_chunk` | 嵌入单个文本块 | 5次，exponential_jitter |
| `embed_single_item` | 嵌入单个项目 | 默认 |
| `rebuild_embeddings` | 批量重建嵌入 | 禁用（快速失败） |
| `generate_podcast` | 生成播客音频 | 默认 |

### 5.2 源处理完整数据流

```mermaid
sequenceDiagram
    participant UI as Frontend
    participant API as API Layer
    participant CMD as Command System
    participant DB as SurrealDB
    participant SG as source_graph
    participant AI as AI Provider
    participant EMB as Embedding Model

    rect rgb(240, 248, 255)
        Note over UI,DB: Step 1: 提交处理请求
        UI->>API: POST /api/sources (file)
        API->>DB: INSERT source (title="Processing...")
        API->>CMD: submit_command("process_source")
        CMD->>DB: INSERT command (status="new")
        API->>DB: UPDATE source.command = command_id
        API-->>UI: 202 Accepted + command_id
    end

    rect rgb(255, 248, 240)
        Note over CMD,EMB: Step 2: Worker 处理
        CMD->>CMD: Worker 获取 command
        CMD->>DB: UPDATE command.status = "running"
        CMD->>SG: source_graph.ainvoke()

        SG->>SG: 提取内容 (PDF/Video/Audio)
        SG->>AI: 生成洞察 (Summary, Topics)
        AI-->>SG: 洞察内容
        SG->>DB: INSERT source_insight

        opt embed=true
            SG->>CMD: submit_command("vectorize_source")
            CMD->>DB: INSERT command (vectorize)

            loop 每个文本块
                CMD->>EMB: 生成嵌入向量
                EMB-->>CMD: embedding vector
                CMD->>DB: INSERT source_embedding
            end
        end

        SG->>DB: UPDATE source (title, full_text, topics)
        SG-->>CMD: 处理结果
        CMD->>DB: UPDATE command.status = "completed"
    end

    rect rgb(240, 255, 240)
        Note over UI,DB: Step 3: 轮询状态
        loop 直到完成
            UI->>API: GET /api/commands/jobs/{id}
            API->>DB: SELECT command WHERE id = $id
            DB-->>API: command record
            API-->>UI: status + progress
        end
    end
```

### 5.3 向量化分层任务模式

```mermaid
graph TB
    subgraph "Parent Task"
        VT[vectorize_source<br/>编排命令]
    end

    subgraph "Child Tasks"
        C1[embed_chunk 1]
        C2[embed_chunk 2]
        C3[embed_chunk 3]
        CN[embed_chunk N]
    end

    subgraph "Processing"
        VT --> SPLIT[文本分块]
        SPLIT --> C1
        SPLIT --> C2
        SPLIT --> C3
        SPLIT --> CN
    end

    subgraph "Concurrency Control"
        POOL[Worker Pool<br/>MAX_TASKS=5]
    end

    C1 --> POOL
    C2 --> POOL
    C3 --> POOL
    CN --> POOL

    POOL --> DB[(SurrealDB<br/>source_embedding)]
```

**代码实现**：

```python
@command("vectorize_source", app="open_notebook", retry=None)
async def vectorize_source_command(input_data):
    # 1. 删除现有嵌入（幂等性）
    await repo_query(
        "DELETE source_embedding WHERE source = $source_id",
        {"source_id": ensure_record_id(input_data.source_id)}
    )

    # 2. 文本分块
    chunks = split_text(source.full_text)

    # 3. 提交每个块作为独立任务
    for idx, chunk_text in enumerate(chunks):
        submit_command(
            "open_notebook",
            "embed_chunk",
            {
                "source_id": input_data.source_id,
                "chunk_index": idx,
                "chunk_text": chunk_text,
            }
        )

    return VectorizeSourceOutput(
        success=True,
        total_chunks=len(chunks),
        jobs_submitted=len(chunks),
    )
```

---

## 6. API 接口

### 6.1 命令管理接口

```mermaid
graph LR
    subgraph "Command API Endpoints"
        POST[POST /api/commands/jobs<br/>提交命令]
        GET_ONE[GET /api/commands/jobs/{id}<br/>查询单个状态]
        GET_LIST[GET /api/commands/jobs<br/>列表查询]
        DELETE[DELETE /api/commands/jobs/{id}<br/>取消命令]
        DEBUG[GET /api/commands/registry/debug<br/>调试注册表]
    end
```

### 6.2 请求与响应模型

**提交命令请求**：
```json
{
  "command": "process_source",
  "app": "open_notebook",
  "input": {
    "source_id": "source:abc123",
    "content_state": {"file_path": "/uploads/doc.pdf"},
    "notebook_ids": ["notebook:xyz"],
    "transformations": [],
    "embed": true
  }
}
```

**状态响应**：
```json
{
  "job_id": "command:01HXYZ...",
  "status": "completed",
  "result": {
    "success": true,
    "source_id": "source:abc123",
    "embedded_chunks": 42,
    "insights_created": 5,
    "processing_time": 12.34
  },
  "error_message": null,
  "created": "2025-01-03T10:00:00Z",
  "updated": "2025-01-03T10:00:12Z"
}
```

---

## 7. 状态查询与关联

### 7.1 Source 与 Command 关联

```mermaid
graph LR
    subgraph "Source Record"
        S[Source]
        S_ID[id: source:abc]
        S_CMD[command: command:xyz]
        S_TITLE[title: "Document.pdf"]
    end

    subgraph "Command Record"
        C[Command]
        C_ID[id: command:xyz]
        C_STATUS[status: completed]
        C_RESULT[result: {...}]
    end

    S_CMD -->|references| C_ID
```

### 7.2 批量状态查询优化

```python
# api/routers/sources.py - 批量获取命令状态
async def get_sources(...):
    # 收集所有 command_ids
    command_ids = [str(row["command"]) for row in result if row.get("command")]

    # 并发获取状态（限制并发数）
    semaphore = asyncio.Semaphore(10)

    async def get_status_with_limit(command_id):
        async with semaphore:
            return await get_command_status(command_id)

    # 批量获取
    status_results = await asyncio.gather(
        *[get_status_with_limit(cmd_id) for cmd_id in command_ids],
        return_exceptions=True
    )
```

---

## 8. 配置与调优

### 8.1 环境变量配置

```bash
# Worker 并发控制
SURREAL_COMMANDS_MAX_TASKS=5          # Worker 池大小

# 重试配置
SURREAL_COMMANDS_RETRY_ENABLED=true   # 启用重试
SURREAL_COMMANDS_RETRY_MAX_ATTEMPTS=3 # 最大重试次数
SURREAL_COMMANDS_RETRY_WAIT_STRATEGY=exponential_jitter  # 重试策略
SURREAL_COMMANDS_RETRY_WAIT_MIN=1     # 最小等待时间(秒)
SURREAL_COMMANDS_RETRY_WAIT_MAX=30    # 最大等待时间(秒)
```

### 8.2 调优场景

```mermaid
graph TB
    subgraph "低资源环境"
        LR_TASKS["MAX_TASKS=2"]
        LR_RETRY["RETRY_MAX_ATTEMPTS=3"]
        LR_WAIT["RETRY_WAIT_MAX=20"]
    end

    subgraph "高性能环境"
        HP_TASKS["MAX_TASKS=10"]
        HP_RETRY["RETRY_MAX_ATTEMPTS=5"]
        HP_WAIT["RETRY_WAIT_MAX=30"]
    end

    subgraph "调试模式"
        DB_RETRY["RETRY_ENABLED=false"]
    end

    LOW[低 CPU/内存] --> LR_TASKS
    LOW --> LR_RETRY
    LOW --> LR_WAIT

    HIGH[高性能服务器] --> HP_TASKS
    HIGH --> HP_RETRY
    HIGH --> HP_WAIT

    DEBUG[问题排查] --> DB_RETRY
```

---

## 9. 事务冲突处理

### 9.1 冲突发生场景

```mermaid
graph TB
    subgraph "并发写入场景"
        W1[Worker 1: embed_chunk 1]
        W2[Worker 2: embed_chunk 2]
        W3[Worker 3: embed_chunk 3]
    end

    subgraph "SurrealDB"
        TX1[Transaction 1]
        TX2[Transaction 2]
        TX3[Transaction 3]
        TABLE[source_embedding table]
    end

    W1 --> TX1
    W2 --> TX2
    W3 --> TX3

    TX1 -->|WRITE| TABLE
    TX2 -->|WRITE| TABLE
    TX3 -->|WRITE| TABLE

    TABLE -->|Conflict!| RETRY[RuntimeError<br/>触发重试]
```

### 9.2 冲突处理流程

```mermaid
flowchart TD
    START[执行数据库写入] --> TRY[尝试提交事务]
    TRY --> CHECK{事务结果?}

    CHECK -->|Success| DONE[完成]
    CHECK -->|Conflict| ERROR[RuntimeError:<br/>"read or write conflict"]

    ERROR --> RERAISE[重新抛出异常]
    RERAISE --> RETRY_MECH[重试机制捕获]
    RETRY_MECH --> BACKOFF[等待退避时间<br/>1s → ~2s → ~4s]
    BACKOFF --> TRY

    RETRY_MECH -->|达到最大次数| FAIL[标记为失败]
```

---

## 10. 完整工作流示例

### 10.1 播客生成流程

```mermaid
sequenceDiagram
    participant UI as Frontend
    participant API as Podcast API
    participant CMD as Command System
    participant DB as SurrealDB
    participant PC as podcast_commands
    participant AI as AI Models
    participant TTS as TTS Service

    UI->>API: POST /api/podcasts
    API->>CMD: submit_command("generate_podcast")
    CMD->>DB: INSERT command (status="new")
    API-->>UI: 202 Accepted + command_id

    Note over CMD,TTS: Worker 处理

    CMD->>DB: UPDATE status="running"
    CMD->>PC: generate_podcast_command()

    PC->>DB: SELECT episode_profile, speaker_profile
    DB-->>PC: 配置数据

    PC->>DB: INSERT podcast_episode (command=command_id)

    PC->>AI: 生成大纲 (Outline Model)
    AI-->>PC: outline

    PC->>AI: 生成脚本 (Transcript Model)
    AI-->>PC: transcript

    loop 每个说话人片段
        PC->>TTS: 生成音频片段
        TTS-->>PC: audio segment
    end

    PC->>PC: 合并音频片段

    PC->>DB: UPDATE podcast_episode (audio_file, transcript, outline)
    PC-->>CMD: PodcastGenerationOutput

    CMD->>DB: UPDATE command (status="completed", result=...)

    UI->>API: GET /api/commands/jobs/{id}
    API->>DB: SELECT command
    API-->>UI: status="completed" + result

    UI->>API: GET /api/podcasts/{episode_id}
    API-->>UI: 播客下载链接
```

---

## 11. 监控与调试

### 11.1 日志输出示例

```
INFO     Starting source processing for source: source:abc123
INFO     Loaded 2 transformations
INFO     Updated source source:abc123 with command reference
INFO     Processing source with 1 notebooks
INFO     Starting vectorization orchestration for source:abc123
INFO     Deleting existing embeddings for source:abc123
INFO     Splitting text into chunks for source:abc123
INFO     Split into 42 chunks
INFO     Submitting 42 chunk jobs to worker queue
INFO       Submitted 42/42 chunk jobs
WARNING  Transaction conflict for chunk 15 - will be retried by retry mechanism
DEBUG    Successfully embedded chunk 15 for source source:abc123
INFO     Successfully processed source: source:abc123 in 12.34s
INFO     Created 5 insights and 42 embedded chunks
```

### 11.2 调试端点

```bash
# 查看已注册的命令
GET /api/commands/registry/debug

# 响应示例
{
  "total_commands": 6,
  "commands_by_app": {
    "open_notebook": [
      "process_source",
      "vectorize_source",
      "embed_chunk",
      "embed_single_item",
      "rebuild_embeddings",
      "generate_podcast"
    ]
  }
}
```

---

## 12. 总结

### 12.1 架构优势

| 优势 | 说明 |
|------|------|
| **解耦** | HTTP 请求与后台处理分离，避免超时 |
| **可靠** | SurrealDB 持久化确保任务不丢失 |
| **可扩展** | Worker Pool 支持水平扩展 |
| **弹性** | 自动重试处理瞬态故障 |
| **可观测** | 命令状态可查询、可追踪 |
| **并发控制** | 通过 Worker Pool 大小控制并发 |

### 12.2 交互模式总结

```mermaid
graph TB
    subgraph "交互模式"
        M1[异步提交模式]
        M2[同步执行模式]
        M3[编排-子任务模式]
    end

    subgraph "适用场景"
        S1[长时间操作<br/>文档处理、播客生成]
        S2[快速操作<br/>测试、调试]
        S3[大规模并行<br/>批量向量化]
    end

    M1 --> S1
    M2 --> S2
    M3 --> S3
```

### 12.3 最佳实践

1. **使用异步模式** - 对于可能超过几秒的操作
2. **配置合理重试** - 针对操作类型选择合适的重试策略
3. **监控重试率** - 高重试率可能表示需要降低并发
4. **利用幂等性** - 编排命令删除现有数据再重建
5. **分层任务** - 大任务拆分为小任务，各自有重试逻辑
