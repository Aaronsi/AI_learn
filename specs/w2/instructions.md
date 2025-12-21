# Instructions

# constitution

这是针对 ./w2/db_query 项目的：

- 后端使用 Ergonomic Python 风格来编写代码， 前端使用typescript
- 前端后端要有严格类型标注。
- 使用pydantic 来定义数据模型
- 所有后端生成的 JSON 数据，使用 camelCase 格式。
- 不需要 authentication, 任何用户都可以使用。

## 基本思路
这是一个数据库查询工具，用户可以添加一个 db url，系统会链接到数据库，获取数据库的 metadata，然后将数据库中的table和view的信息展示出来，然后用户可以自己输入 sql 查询，也可以通过自然语言来生成 sql 查询。

基本想法：
- 数据库链接字符串和数据库的metadata 都会存储到sqlite数据库中。我们可以根据 postgres的功能来查询系统中的表和视图的信息，然后用LLM来讲这些信息转换成json 格式，然后存储到sqlite数据库中。这个信息以后可以复用。
- 当用户使用LLM 来生成查询时，我们可以把系统中的表和视图的信息作为context传递给LLM，然后LLM会根据这些信息来生成sql 查询。
- 任何输入的sql 语句，都需要经过sqlparser解析，确保语法正确，并且仅包含select语句。如果语法不正确，需要给出错误信息。
  - 如果查询不包含limit子句，则默认添加 limit 1000 子句。
- 输出格式是json，前端将其组织成表格，并显示出来。

后端使用Python （uv）/ FastAPI / sqlglot /openai sdk 来实现。
前端使用React / refine 5 / tailwind / ant design 来实现。sql editor 使用 monaco editor 来实现。

DeepSeek API key 在环境变量DeepSeek_API_KEY 中。数据库链接和metadata存储在sqlite数据库中，放在~/.db_query/db_query.db中。

后端 API需要支持cors，允许所有的origin。
大致API如下：

'''ba
# 获取所有已存储的数据库
GET /api/v1/dbs

# 添加一个数据库
PUT /api/v1/dbs/{name}
{
  "url":"postgres://postgres:postgres@localhost:5432/postgres"
}

# 获取一个数据库的metadata
GET /api/v1/dbs/{name}

# 查询某个数据库的信息
POST /api/v1/dbs/{name}/query
{
  "sql":"SELECT * FROM users"
}

# 根据自然语言生成sql
POST /api/v1/dbs/{name}/query/natural
{
  "prompt":"查询用户表的所有信息"
}
'''

# 测试
运行后端和前端，根据@w2/db_query/test.rest 用curl测试后端已实现的路由；然后用playwright 代开前端进行测试，任何测试问题，think ultra hard and fix

## 优化UI

## 前端风格
使用 style.md 中的风格，学习 ./site 中 token 的定义，优化整体的 UI和UX。

左边增加数据库删除操作；
点击某个数据库名称前面的图标，要显示数据库下面的表，点击表前面的图标要显示表下面的列信息；
查询结果框要放在SQL编辑器下面；

1.删除数据库操作不管用；
2.点击某个数据库名称前面的图标，要显示数据库下面的表，点击表前面的图标要显示表下面的列信息；增加后端接口来实现使用功能；

1.添加数据库弹出框，不需要上一步和下一步按钮；只需要“取消”，“测试连接”和“完成”按钮；
2.点击“取消”按钮，直接关闭添加数据库弹出框；
3.点击“测试连接”按钮，测试数据库是否能够连接通过；并提示连接结果信息；
4.点击“完成”按钮，先判断数据库信息是否填写完整；再判断数据库链接是否正常；如果数据库信息填写完整并且数据库链接正常，则关闭添加数据库弹出框；并将添加成功的数据库添加到左边数据库列表中。

1.数据库名字要放在数据库图标后面，放在一行；
2.自然语言查询需要访问deepseek模型api接口，生成对应的sql，并放入sql编辑器的sql输入框中。

1.数据库名字要放在数据库图标后面，放在一行；
2.点击生成sql按钮，报错，提示“生成sql失败”

表名前面需要增加表的图标；

## review
/speckit.analyze 仔细 review w2/db_query 代码，删除不用的代码，添加更多 unit test，以及寻找 opportunity
do all of these

## week 2 ：homework

1. 完善文档。  /speckit.implement phase 4
2. 已经完成 phase 1-3 的功能，但是还有类似 export csv/json 的功能没完成，使用 speckit 来添加这个功能。





## --------------------------------项目网站维护---------------------------------------------------------
## 撰写介绍，更新到项目网站中
/clear

project 2 已完成，截图见 @site/public/projects/project-2/preview.jpg 请更新./sites 下面的 project页面，并且更新 project 2 页面，根据 @specs/001-db-query-tool/spec.md 和 @specs/001-db-query-tool/plan.md 撰写详细介绍。

## 记录最终界面样子
使用playwright 打开 todo  网址，选择 todo db，然后输入 sql：
todo
点击execute，然后截图放在  ./site/public/project-2/preview.png

## 网站代码提交
submit pr



### 切换到claude code
仔细阅读 ./w2/db_query 下面的代码，然后运行后端和前端，根据 @w2/db_query/fixtures/test.rest 用curl 测试后端已实现的路由；然后用 playwright代开前端进行测试，任何测试问题， think ultra hard and fix.


## 添加MySQL db 支持
参考 ./w2/db_query/backend 中的PostgreSQL 实现，实现MySQL 的 metadata 提取和查询支持，同时自然语言生成 sql 也支持MySQL。目前我本地有一个 chapter1 数据库，数据库链接为mysql://root:root@localhost:3306/chapter1。 

构建一个相对复杂的mysql 数据库 interview_db,记录公司招聘面试安排面试结果等相关的信息，并添加足够丰富且真实的 seed data。

## 测试 MySQL db支持
目前mysql已经得到支持，在 ./w2/db_query/fixtures/test.rest 中添加 MySQL db 支持的测试用例，然后运行测试。如果后端测试 ok， 那么打开后端和前端，使用playwright 测试前端，确保 MySQL db 的基本功能：

- 添加 新的数据库 chapter1（url为mysql://root:root@localhost:3306/chapter1）
- 生成查询 chapter1，并显示结果
- 自然语言生成 MySQL sql，查询  chapter1, 并显示结果

