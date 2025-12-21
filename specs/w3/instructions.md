# Instructions

## create a new agent
你是一个 Python 开发的资深系统级工程师，可以进行优雅的架构设计，遵循 Python 哲学，并对并发异步web/grpc/数据库/大数据处理有深刻的理解。
### agent-py-arch 使用
go ahad to check arch for ./w1/. List all imporvements.

## code review command

帮我参照 @.claude/commands/speckit.specify.md 的结构，think ultra hard, 构建一个对python 和 Typescript 代码进行深度代码审查的命令，放在 @.claude/commands/ 下。主要考虑以下几个方面：
- 架构和设计：是否考虑python 和 typescript 的架构和设计最佳实践？是否有清晰的接口设计？是否考虑一定程度的可扩展性
- KISS 原则
- 代码质量：DRY, YAGNI, SOLID, etc. 函数原则上不超过 150行， 参数原则上不超过 7 各。
- 使用 builder 模式


### 使用
/codereview ./w2/db_query
write this as a whole in ./specs/w3/001-code-review.md
