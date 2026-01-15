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

## Raflow spec format

将@specs/w3/raflow/0001-spec.md 的内容组织成格式正确的 markdown 文件，不要丢失任何内容。

## 构建详细的设计文档

根据 @specs/w3/raflow/0001-spec.md 的内容， 进行系统的 web search 确保信息的准确性，尤其是使用最新版本的 dependencies。根据你了解的知识，构建一个详细的设计文档，放在 ./specs/w3/raflow/0002-design.md 文件中，输出为中文, 使用 mermaid 绘制架构，设计，组件，流程等图表并详细说明。

## 生成实现计划

根据这个设计生成 implementation plan，保存在 ./specs/w3/raflow/0003-implementation-plan.md

## 实现
根据 @specs/w3/raflow/002-design.md 和 ./specs/w3/raflow/0003-implementation-plan.md 文件中的设计，在w3/raflow项目的基本代码结构基础上，完整实现 phrase 1。


根据 @specs/w3/raflow/002-design.md 和 ./specs/w3/raflow/0003-implementation-plan.md 文件中的设计，在w3/raflow项目的基本代码结构基础上，完整实现 phrase 2。

## 重新生成设计文档

仔细阅读目前 ./w3/raflow 的代码think ultra hard，构建一个更新的 design doc, 放在 ./specs/w3/raflow/0004-design.md 文件中，输出为中文，使用 mermaid 绘制架构，设计，组件，流程等图表并详细说明。

cargo tauri dev

请根据 @specs/w3/raflow/002-design.md 和 ./specs/w3/raflow/0003-implementation-plan.md 文件中的设计，检查w3/raflow项目代码，在启动后，录入语音，却一直停留在处理中，无法将语音转化为文字写入文本框的问题。

请根据 @specs/w3/raflow/002-design.md 和 ./specs/w3/raflow/0003-implementation-plan.md 文件中的设计，检查w3/raflow项目代码，在启动后，录入语音，报C:\Users\aaron\Downloads\unknown_error.png和C:\Users\aaron\Downloads\后台日志.png图片中错误的问题。

请根据 ./specs/w3/raflow/002-design.md 和 ./specs/w3/raflow/0003-implementation-plan.md 文件中的设计，检查w3/raflow项目代码，在启动后，录入语音，报C:\Users\aaron\Downloads\unknown_error.png和C:\Users\aaron\Downloads\页面报错.png图片中错误的问题。

请根据 ./specs/w3/raflow/002-design.md 和 ./specs/w3/raflow/0003-implementation-plan.md 文件中的设计，think ultra hard,检查w3/raflow项目代码，为什么在项目启动后，页面录入语音，报C:\Users\aaron\Downloads\页面报错.png图片中错误的问题。同时整体代码review下，排查是否还有别的问题，确保应用正确使用。

请根据 ./specs/w3/raflow/002-design.md 和 ./specs/w3/raflow/0003-implementation-plan.md 文件中的设计，think ultra hard,检查w3/raflow项目代码，为什么在项目启动后，页面录入语音，报截图中的错误。同时整体代码review下，排查是否还有别的问题，确保应用正确使用。

请根据 ./specs/w3/raflow/002-design.md 和 ./specs/w3/raflow/0003-implementation-plan.md 文件中的设计，think ultra hard,检查w3/raflow项目代码，为什么在项目启动后，点击 开始录音 按钮，录音完毕，点击 停止录音 按钮后，状态显示为处理中，没有将录音转换为文字并显示出来；并且最后左上角状态又恢复为了 就绪。请 think ultra hard 修复该问题。同时整体代码review下，排查是否还有别的问题，确保应用正确使用。

请根据 ./specs/w3/raflow/002-design.md 和 ./specs/w3/raflow/0003-implementation-plan.md 文件中的设计，think ultra hard,检查w3/raflow项目代码，为什么在项目启动后，点击 开始录音 按钮，录音完毕，点击 停止录音 按钮后，状态显示为处理中，没有将录音转换为文字并显示出来；并且最后左上角状态又恢复为了 就绪，但还是没有将录音转换为文字并显示出来。请根据控制台打印日志 think ultra hard 修复该问题。

请根据 ./specs/w3/raflow/002-design.md 和 ./specs/w3/raflow/0003-implementation-plan.md 文件中的设计，think ultra hard,检查w3/raflow项目代码，为什么在项目启动后，点击 开始录音 按钮，录音完毕，点击 停止录音 按钮后，状态显示为处理中，没有将录音转换为文字并显示出来；并且最后左上角状态又恢复为了 就绪，但还是没有将录音转换为文字并显示出来。请根据控制台打印日志C:\Users\aaron\Downloads\页面报错.png图片，C:\Users\aaron\Downloads\页面报错1.png图片和C:\Users\aaron\Downloads\页面报错2.png图片来分析问题并解决问题。

请根据 ./specs/w3/raflow/002-design.md 和 ./specs/w3/raflow/0003-implementation-plan.md 文件中的设计，think ultra hard,检查w3/raflow项目代码，为什么在项目启动后，点击 开始录音 按钮，录音完毕，点击 停止录音 按钮后，状态显示为处理中，没有将录音转换为文字并显示出来；并且最后左上角状态又恢复为了 就绪，但还是没有将录音转换为文字并显示出来。请根据控制台打印日志C:\Users\aaron\Downloads\页面报错.png图片和C:\Users\aaron\Downloads\页面报错1.png图片来分析问题并解决问题。

请根据 ./specs/w3/raflow/002-design.md 和 ./specs/w3/raflow/0003-implementation-plan.md 文件中的设计，think ultra hard,检查w3/raflow项目代码，为什么在项目启动后，点击 开始录音 按钮，录音完毕，点击 停止录音 按钮后，状态显示为处理中，没有将录音转换为文字并显示出来；并且最后左上角状态又恢复为了 就绪，再变为了 错误；如图C:\Users\aaron\Downloads\页面报错.png所示。

