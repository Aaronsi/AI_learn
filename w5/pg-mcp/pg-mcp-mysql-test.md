# pg-mcp MySQL 测试用例文档

## 数据库信息

- **MySQL 连接**: `mysql://root:root@123@localhost:3306/mysql`
- **测试数据库**: 
  - `chapter1` - 教学管理系统数据库
  - `sql_homework` - SQL作业数据库

---

## chapter1 数据库表结构

### student (学生表)
- `Sno` (char(3), PK) - 学号
- `Sname` (char(4)) - 姓名
- `Ssex` (char(2)) - 性别
- `Sbirthday` (datetime) - 出生日期
- `Class` (char(5)) - 班级

### course (课程表)
- `Cno` (char(5), PK) - 课程号
- `Cname` (varchar(10)) - 课程名
- `Tno` (char(3)) - 教师编号

### sc (选课表)
- `Sno` (char(3)) - 学号
- `Cno` (char(5)) - 课程号
- `Grade` (decimal(5,2)) - 成绩

### teacher (教师表)
- `Tno` (char(3), PK) - 教师编号
- `Tname` (char(4)) - 姓名
- `Tsex` (char(2)) - 性别
- `Tbirthday` (datetime) - 出生日期
- `Prof` (char(6)) - 职称
- `Depart` (varchar(10)) - 所在系

### 月度代销商品 (月度代销商品表)
- `代销商` (varchar(20)) - 代销商名称
- `产品` (varchar(20)) - 产品名称
- `价格` (decimal(10,1)) - 价格
- `月份` (varchar(20)) - 月份

---

## 测试用例分类

### 一、简单查询 (基础 SELECT)

#### 1.1 单表查询

**用例 1.1.1**: 查询所有学生信息
```
查询所有学生的信息
```
**预期 SQL**: `SELECT * FROM student`

**用例 1.1.2**: 查询所有学生的姓名和学号
```
查询所有学生的姓名和学号
```
**预期 SQL**: `SELECT Sname, Sno FROM student`

**用例 1.1.3**: 查询所有课程名称
```
查询所有课程的名称
```
**预期 SQL**: `SELECT Cname FROM course`

**用例 1.1.4**: 查询所有教师信息
```
查询所有教师的信息
```
**预期 SQL**: `SELECT * FROM teacher`

**用例 1.1.5**: 查询所有代销商名称
```
查询所有代销商的名称
```
**预期 SQL**: `SELECT DISTINCT 代销商 FROM 月度代销商品`

---

#### 1.2 条件查询 (WHERE)

**用例 1.2.1**: 查询性别为男的学生
```
查询所有男学生的信息
```
**预期 SQL**: `SELECT * FROM student WHERE Ssex = '男'`

**用例 1.2.2**: 查询计算机系的学生
```
查询计算机系的所有学生
```
**预期 SQL**: `SELECT * FROM student WHERE Class LIKE '%计算机%'`

**用例 1.2.3**: 查询成绩大于80分的选课记录
```
查询成绩大于80分的选课记录
```
**预期 SQL**: `SELECT * FROM sc WHERE Grade > 80`

**用例 1.2.4**: 查询副教授职称的教师
```
查询所有副教授的信息
```
**预期 SQL**: `SELECT * FROM teacher WHERE Prof = '副教授'`

**用例 1.2.5**: 查询2019年7月的代销商品
```
查询2019年7月的所有代销商品记录
```
**预期 SQL**: `SELECT * FROM 月度代销商品 WHERE 月份 = '2019-07'`

**用例 1.2.6**: 查询价格在10到20之间的商品
```
查询价格在10到20之间的代销商品
```
**预期 SQL**: `SELECT * FROM 月度代销商品 WHERE 价格 BETWEEN 10 AND 20`

**用例 1.2.7**: 查询姓张的学生
```
查询所有姓张的学生
```
**预期 SQL**: `SELECT * FROM student WHERE Sname LIKE '张%'`

---

#### 1.3 排序查询 (ORDER BY)

**用例 1.3.1**: 按学号升序查询所有学生
```
按学号从小到大查询所有学生
```
**预期 SQL**: `SELECT * FROM student ORDER BY Sno ASC`

**用例 1.3.2**: 按成绩降序查询选课记录
```
按成绩从高到低查询所有选课记录
```
**预期 SQL**: `SELECT * FROM sc ORDER BY Grade DESC`

**用例 1.3.3**: 按出生日期查询学生，年龄大的在前
```
按出生日期从早到晚查询学生信息
```
**预期 SQL**: `SELECT * FROM student ORDER BY Sbirthday ASC`

**用例 1.3.4**: 按价格和月份排序查询代销商品
```
按价格从高到低，月份从早到晚查询代销商品
```
**预期 SQL**: `SELECT * FROM 月度代销商品 ORDER BY 价格 DESC, 月份 ASC`

---

#### 1.4 限制结果数量 (LIMIT)

**用例 1.4.1**: 查询前5个学生
```
查询前5个学生的信息
```
**预期 SQL**: `SELECT * FROM student LIMIT 5`

**用例 1.4.2**: 查询成绩最高的3条记录
```
查询成绩最高的3条选课记录
```
**预期 SQL**: `SELECT * FROM sc ORDER BY Grade DESC LIMIT 3`

---

### 二、聚合查询 (GROUP BY, 聚合函数)

#### 2.1 计数查询

**用例 2.1.1**: 统计学生总数
```
统计一共有多少学生
```
**预期 SQL**: `SELECT COUNT(*) FROM student`

**用例 2.1.2**: 统计男学生人数
```
统计有多少个男学生
```
**预期 SQL**: `SELECT COUNT(*) FROM student WHERE Ssex = '男'`

**用例 2.1.3**: 统计每个班级的学生人数
```
统计每个班级有多少学生
```
**预期 SQL**: `SELECT Class, COUNT(*) FROM student GROUP BY Class`

**用例 2.1.4**: 统计每个代销商的商品种类数
```
统计每个代销商有多少种产品
```
**预期 SQL**: `SELECT 代销商, COUNT(DISTINCT 产品) FROM 月度代销商品 GROUP BY 代销商`

---

#### 2.2 求和/平均值查询

**用例 2.2.1**: 计算所有学生的平均成绩
```
计算所有学生的平均成绩
```
**预期 SQL**: `SELECT AVG(Grade) FROM sc`

**用例 2.2.2**: 计算每个学生的总成绩
```
计算每个学生的总成绩
```
**预期 SQL**: `SELECT Sno, SUM(Grade) FROM sc GROUP BY Sno`

**用例 2.2.3**: 计算每个课程的平均成绩
```
计算每门课程的平均成绩
```
**预期 SQL**: `SELECT Cno, AVG(Grade) FROM sc GROUP BY Cno`

**用例 2.2.4**: 计算每个代销商的总销售额
```
计算每个代销商的总销售额
```
**预期 SQL**: `SELECT 代销商, SUM(价格) FROM 月度代销商品 GROUP BY 代销商`

**用例 2.2.5**: 计算每个产品的平均价格
```
计算每个产品的平均价格
```
**预期 SQL**: `SELECT 产品, AVG(价格) FROM 月度代销商品 GROUP BY 产品`

---

#### 2.3 最大值/最小值查询

**用例 2.3.1**: 查询最高成绩
```
查询最高成绩是多少
```
**预期 SQL**: `SELECT MAX(Grade) FROM sc`

**用例 2.3.2**: 查询每个课程的最高分和最低分
```
查询每门课程的最高分和最低分
```
**预期 SQL**: `SELECT Cno, MAX(Grade), MIN(Grade) FROM sc GROUP BY Cno`

**用例 2.3.3**: 查询每个代销商最贵的商品价格
```
查询每个代销商最贵的商品价格
```
**预期 SQL**: `SELECT 代销商, MAX(价格) FROM 月度代销商品 GROUP BY 代销商`

---

#### 2.4 HAVING 子句

**用例 2.4.1**: 查询平均成绩大于80的课程
```
查询平均成绩大于80分的课程
```
**预期 SQL**: `SELECT Cno, AVG(Grade) FROM sc GROUP BY Cno HAVING AVG(Grade) > 80`

**用例 2.4.2**: 查询选课超过3门的学生
```
查询选课超过3门的学生
```
**预期 SQL**: `SELECT Sno, COUNT(*) FROM sc GROUP BY Sno HAVING COUNT(*) > 3`

**用例 2.4.3**: 查询总销售额超过100的代销商
```
查询总销售额超过100的代销商
```
**预期 SQL**: `SELECT 代销商, SUM(价格) FROM 月度代销商品 GROUP BY 代销商 HAVING SUM(价格) > 100`

---

### 三、多表连接查询 (JOIN)

#### 3.1 内连接 (INNER JOIN)

**用例 3.1.1**: 查询学生选课信息（包含学生姓名和课程名）
```
查询所有学生的选课信息，显示学生姓名和课程名
```
**预期 SQL**: 
```sql
SELECT s.Sname, c.Cname, sc.Grade 
FROM sc 
INNER JOIN student s ON sc.Sno = s.Sno 
INNER JOIN course c ON sc.Cno = c.Cno
```

**用例 3.1.2**: 查询每门课程的授课教师姓名
```
查询每门课程的授课教师姓名
```
**预期 SQL**: 
```sql
SELECT c.Cname, t.Tname 
FROM course c 
INNER JOIN teacher t ON c.Tno = t.Tno
```

**用例 3.1.3**: 查询学生姓名、课程名和成绩
```
查询学生姓名、课程名和对应的成绩
```
**预期 SQL**: 
```sql
SELECT s.Sname, c.Cname, sc.Grade 
FROM sc 
JOIN student s ON sc.Sno = s.Sno 
JOIN course c ON sc.Cno = c.Cno
```

---

#### 3.2 左连接 (LEFT JOIN)

**用例 3.2.1**: 查询所有学生及其选课情况（包括未选课的学生）
```
查询所有学生及其选课情况，包括没有选课的学生
```
**预期 SQL**: 
```sql
SELECT s.Sname, c.Cname, sc.Grade 
FROM student s 
LEFT JOIN sc ON s.Sno = sc.Sno 
LEFT JOIN course c ON sc.Cno = c.Cno
```

**用例 3.2.2**: 查询所有课程及其选课情况（包括无人选的课程）
```
查询所有课程及其选课情况，包括没有人选的课程
```
**预期 SQL**: 
```sql
SELECT c.Cname, s.Sname, sc.Grade 
FROM course c 
LEFT JOIN sc ON c.Cno = sc.Cno 
LEFT JOIN student s ON sc.Sno = s.Sno
```

---

#### 3.3 多表连接

**用例 3.3.1**: 查询学生姓名、课程名、教师姓名和成绩
```
查询学生姓名、课程名、授课教师姓名和成绩
```
**预期 SQL**: 
```sql
SELECT s.Sname, c.Cname, t.Tname, sc.Grade 
FROM sc 
JOIN student s ON sc.Sno = s.Sno 
JOIN course c ON sc.Cno = c.Cno 
JOIN teacher t ON c.Tno = t.Tno
```

**用例 3.3.2**: 查询计算机系的学生及其选课信息
```
查询计算机系的学生及其选课信息
```
**预期 SQL**: 
```sql
SELECT s.Sname, c.Cname, sc.Grade 
FROM student s 
JOIN sc ON s.Sno = sc.Sno 
JOIN course c ON sc.Cno = c.Cno 
WHERE s.Class LIKE '%计算机%'
```

---

### 四、子查询 (Subquery)

#### 4.1 标量子查询

**用例 4.1.1**: 查询成绩高于平均成绩的选课记录
```
查询成绩高于平均成绩的选课记录
```
**预期 SQL**: 
```sql
SELECT * FROM sc 
WHERE Grade > (SELECT AVG(Grade) FROM sc)
```

**用例 4.1.2**: 查询年龄最大的学生信息
```
查询年龄最大的学生信息
```
**预期 SQL**: 
```sql
SELECT * FROM student 
WHERE Sbirthday = (SELECT MIN(Sbirthday) FROM student)
```

---

#### 4.2 IN 子查询

**用例 4.2.1**: 查询选修了某门课程的学生
```
查询选修了课程号为'001'的所有学生信息
```
**预期 SQL**: 
```sql
SELECT * FROM student 
WHERE Sno IN (SELECT Sno FROM sc WHERE Cno = '001')
```

**用例 4.2.2**: 查询计算机系教师所授课程的学生选课情况
```
查询计算机系教师所授课程的学生选课情况
```
**预期 SQL**: 
```sql
SELECT * FROM sc 
WHERE Cno IN (
    SELECT Cno FROM course 
    WHERE Tno IN (
        SELECT Tno FROM teacher WHERE Depart = '计算机系'
    )
)
```

---

#### 4.3 EXISTS 子查询

**用例 4.3.1**: 查询有选课记录的学生
```
查询有选课记录的学生信息
```
**预期 SQL**: 
```sql
SELECT * FROM student s 
WHERE EXISTS (SELECT 1 FROM sc WHERE sc.Sno = s.Sno)
```

**用例 4.3.2**: 查询没有选课的学生
```
查询没有选课的学生信息
```
**预期 SQL**: 
```sql
SELECT * FROM student s 
WHERE NOT EXISTS (SELECT 1 FROM sc WHERE sc.Sno = s.Sno)
```

---

### 五、复杂查询组合

#### 5.1 多条件组合

**用例 5.1.1**: 查询计算机系男学生的选课信息
```
查询计算机系男学生的选课信息，显示学生姓名、课程名和成绩
```
**预期 SQL**: 
```sql
SELECT s.Sname, c.Cname, sc.Grade 
FROM student s 
JOIN sc ON s.Sno = sc.Sno 
JOIN course c ON sc.Cno = c.Cno 
WHERE s.Class LIKE '%计算机%' AND s.Ssex = '男'
```

**用例 5.1.2**: 查询成绩在80到90之间的选课记录，按成绩降序排列
```
查询成绩在80到90之间的选课记录，按成绩从高到低排列
```
**预期 SQL**: 
```sql
SELECT * FROM sc 
WHERE Grade BETWEEN 80 AND 90 
ORDER BY Grade DESC
```

---

#### 5.2 分组与排序组合

**用例 5.2.1**: 查询每个学生的平均成绩，按平均成绩降序排列
```
查询每个学生的平均成绩，按平均成绩从高到低排列
```
**预期 SQL**: 
```sql
SELECT Sno, AVG(Grade) as avg_grade 
FROM sc 
GROUP BY Sno 
ORDER BY avg_grade DESC
```

**用例 5.2.2**: 查询每个代销商每个月的总销售额，按代销商和月份排序
```
查询每个代销商每个月的总销售额，按代销商和月份排序
```
**预期 SQL**: 
```sql
SELECT 代销商, 月份, SUM(价格) as total 
FROM 月度代销商品 
GROUP BY 代销商, 月份 
ORDER BY 代销商, 月份
```

---

#### 5.3 多表连接 + 聚合

**用例 5.3.1**: 查询每个学生的选课门数和平均成绩
```
查询每个学生的选课门数和平均成绩，显示学生姓名
```
**预期 SQL**: 
```sql
SELECT s.Sname, COUNT(sc.Cno) as course_count, AVG(sc.Grade) as avg_grade 
FROM student s 
LEFT JOIN sc ON s.Sno = sc.Sno 
GROUP BY s.Sno, s.Sname
```

**用例 5.3.2**: 查询每门课程的选课人数和平均成绩
```
查询每门课程的选课人数和平均成绩，显示课程名
```
**预期 SQL**: 
```sql
SELECT c.Cname, COUNT(sc.Sno) as student_count, AVG(sc.Grade) as avg_grade 
FROM course c 
LEFT JOIN sc ON c.Cno = sc.Cno 
GROUP BY c.Cno, c.Cname
```

**用例 5.3.3**: 查询每个代销商的产品种类数和平均价格
```
查询每个代销商的产品种类数和平均价格
```
**预期 SQL**: 
```sql
SELECT 代销商, COUNT(DISTINCT 产品) as product_count, AVG(价格) as avg_price 
FROM 月度代销商品 
GROUP BY 代销商
```

---

#### 5.4 复杂子查询

**用例 5.4.1**: 查询成绩高于该课程平均成绩的选课记录
```
查询成绩高于该课程平均成绩的选课记录
```
**预期 SQL**: 
```sql
SELECT sc1.* 
FROM sc sc1 
WHERE sc1.Grade > (
    SELECT AVG(sc2.Grade) 
    FROM sc sc2 
    WHERE sc2.Cno = sc1.Cno
)
```

**用例 5.4.2**: 查询选课门数最多的学生信息
```
查询选课门数最多的学生信息
```
**预期 SQL**: 
```sql
SELECT * FROM student 
WHERE Sno IN (
    SELECT Sno FROM sc 
    GROUP BY Sno 
    HAVING COUNT(*) = (
        SELECT MAX(course_count) 
        FROM (
            SELECT COUNT(*) as course_count 
            FROM sc 
            GROUP BY Sno
        ) as temp
    )
)
```

---

### 六、日期和时间查询

**用例 6.1**: 查询1990年以后出生的学生
```
查询1990年以后出生的学生信息
```
**预期 SQL**: 
```sql
SELECT * FROM student 
WHERE YEAR(Sbirthday) > 1990
```

**用例 6.2**: 查询年龄在20到25岁之间的学生
```
查询年龄在20到25岁之间的学生
```
**预期 SQL**: 
```sql
SELECT * FROM student 
WHERE TIMESTAMPDIFF(YEAR, Sbirthday, CURDATE()) BETWEEN 20 AND 25
```

**用例 6.3**: 查询本月生日的学生
```
查询本月生日的学生信息
```
**预期 SQL**: 
```sql
SELECT * FROM student 
WHERE MONTH(Sbirthday) = MONTH(CURDATE())
```

---

### 七、字符串函数查询

**用例 7.1**: 查询学生姓名长度
```
查询所有学生的姓名和姓名长度
```
**预期 SQL**: 
```sql
SELECT Sname, CHAR_LENGTH(Sname) as name_length 
FROM student
```

**用例 7.2**: 查询姓名包含特定字符的学生
```
查询姓名中包含"张"字的学生
```
**预期 SQL**: 
```sql
SELECT * FROM student 
WHERE Sname LIKE '%张%'
```

---

### 八、CASE WHEN 条件查询

**用例 8.1**: 查询学生成绩等级
```
查询选课记录，显示成绩等级：90以上为优秀，80-89为良好，60-79为及格，60以下为不及格
```
**预期 SQL**: 
```sql
SELECT Sno, Cno, Grade,
    CASE 
        WHEN Grade >= 90 THEN '优秀'
        WHEN Grade >= 80 THEN '良好'
        WHEN Grade >= 60 THEN '及格'
        ELSE '不及格'
    END as grade_level
FROM sc
```

---

### 九、UNION 查询

**用例 9.1**: 查询所有学生和教师的姓名
```
查询所有学生和教师的姓名
```
**预期 SQL**: 
```sql
SELECT Sname as name FROM student
UNION
SELECT Tname as name FROM teacher
```

---

### 十、窗口函数查询（MySQL 8.0+）

**用例 10.1**: 查询每个学生的成绩排名
```
查询每个学生的选课成绩，并显示在该课程中的排名
```
**预期 SQL**: 
```sql
SELECT Sno, Cno, Grade,
    RANK() OVER (PARTITION BY Cno ORDER BY Grade DESC) as rank_in_course
FROM sc
```

**用例 10.2**: 查询每个代销商的价格排名
```
查询每个代销商的商品，按价格从高到低排名
```
**预期 SQL**: 
```sql
SELECT 代销商, 产品, 价格,
    ROW_NUMBER() OVER (PARTITION BY 代销商 ORDER BY 价格 DESC) as price_rank
FROM 月度代销商品
```

---

### 十一、复杂业务场景查询

**用例 11.1**: 查询每个学生的选课情况统计
```
查询每个学生的选课情况，包括学生姓名、选课门数、总成绩、平均成绩、最高分和最低分
```
**预期 SQL**: 
```sql
SELECT 
    s.Sname,
    COUNT(sc.Cno) as course_count,
    SUM(sc.Grade) as total_grade,
    AVG(sc.Grade) as avg_grade,
    MAX(sc.Grade) as max_grade,
    MIN(sc.Grade) as min_grade
FROM student s
LEFT JOIN sc ON s.Sno = sc.Sno
GROUP BY s.Sno, s.Sname
```

**用例 11.2**: 查询每门课程的统计信息
```
查询每门课程的统计信息，包括课程名、选课人数、平均成绩、最高分、最低分
```
**预期 SQL**: 
```sql
SELECT 
    c.Cname,
    COUNT(sc.Sno) as student_count,
    AVG(sc.Grade) as avg_grade,
    MAX(sc.Grade) as max_grade,
    MIN(sc.Grade) as min_grade
FROM course c
LEFT JOIN sc ON c.Cno = sc.Cno
GROUP BY c.Cno, c.Cname
```

**用例 11.3**: 查询每个代销商的月度销售趋势
```
查询每个代销商每个月的销售总额，按月份排序
```
**预期 SQL**: 
```sql
SELECT 代销商, 月份, SUM(价格) as monthly_total
FROM 月度代销商品
GROUP BY 代销商, 月份
ORDER BY 代销商, 月份
```

**用例 11.4**: 查询成绩优秀的学生（平均成绩>=90）
```
查询平均成绩大于等于90分的学生信息
```
**预期 SQL**: 
```sql
SELECT s.*, AVG(sc.Grade) as avg_grade
FROM student s
JOIN sc ON s.Sno = sc.Sno
GROUP BY s.Sno
HAVING AVG(sc.Grade) >= 90
```

**用例 11.5**: 查询每个系的学生人数和平均年龄
```
查询每个系的学生人数和平均年龄
```
**预期 SQL**: 
```sql
SELECT 
    Class,
    COUNT(*) as student_count,
    AVG(TIMESTAMPDIFF(YEAR, Sbirthday, CURDATE())) as avg_age
FROM student
GROUP BY Class
```

---

### 十二、模糊查询和模式匹配

**用例 12.1**: 查询姓名以特定字符开头的学生
```
查询姓名以"李"开头的学生
```
**预期 SQL**: 
```sql
SELECT * FROM student WHERE Sname LIKE '李%'
```

**用例 12.2**: 查询课程名包含特定关键词的课程
```
查询课程名中包含"数据库"的课程
```
**预期 SQL**: 
```sql
SELECT * FROM course WHERE Cname LIKE '%数据库%'
```

---

### 十三、NULL 值处理

**用例 13.1**: 查询没有成绩的选课记录
```
查询没有成绩的选课记录
```
**预期 SQL**: 
```sql
SELECT * FROM sc WHERE Grade IS NULL
```

**用例 13.2**: 查询有成绩的选课记录
```
查询有成绩的选课记录
```
**预期 SQL**: 
```sql
SELECT * FROM sc WHERE Grade IS NOT NULL
```

---

### 十四、去重查询

**用例 14.1**: 查询所有不重复的课程号
```
查询所有不重复的课程号
```
**预期 SQL**: 
```sql
SELECT DISTINCT Cno FROM course
```

**用例 14.2**: 查询所有不重复的代销商和产品组合
```
查询所有不重复的代销商和产品组合
```
**预期 SQL**: 
```sql
SELECT DISTINCT 代销商, 产品 FROM 月度代销商品
```

---

### 十五、分页查询

**用例 15.1**: 查询第1页的学生信息（每页10条）
```
查询第1页的学生信息，每页10条
```
**预期 SQL**: 
```sql
SELECT * FROM student LIMIT 10 OFFSET 0
```

**用例 15.2**: 查询第2页的学生信息（每页10条）
```
查询第2页的学生信息，每页10条
```
**预期 SQL**: 
```sql
SELECT * FROM student LIMIT 10 OFFSET 10
```

---

## 测试执行说明

### 配置 pg-mcp 连接 MySQL

在 `pg-mcp.yaml` 配置文件中添加：

```yaml
databases:
  - name: "chapter1"
    db_type: "mysql"
    host: "localhost"
    port: 3306
    database: "chapter1"
    username: "root"
    password: "root@123"
    schemas:
      - "chapter1"
    min_pool_size: 2
    max_pool_size: 10
  
  - name: "sql_homework"
    db_type: "mysql"
    host: "localhost"
    port: 3306
    database: "sql_homework"
    username: "root"
    password: "root@123"
    schemas:
      - "sql_homework"
    min_pool_size: 2
    max_pool_size: 10
```

### 测试方法

1. **启动 pg-mcp 服务**
2. **使用 MCP 客户端调用 `query` 工具**
3. **传入自然语言查询和数据库名称**
4. **验证生成的 SQL 是否符合预期**
5. **执行 SQL 验证结果正确性**

### 测试示例

```json
{
  "query": "查询所有学生的信息",
  "database": "chapter1",
  "schema": "chapter1",
  "return_type": "result"
}
```

---

## 注意事项

1. **MySQL 语法特性**：
   - 字符串使用单引号 `'`
   - `LIMIT` 语法：`LIMIT n OFFSET m` 或 `LIMIT m, n`
   - 日期函数：`YEAR()`, `MONTH()`, `TIMESTAMPDIFF()`
   - 字符串函数：`CHAR_LENGTH()`, `CONCAT()`

2. **中文表名和列名**：
   - 某些表使用中文名称（如 `月度代销商品`）
   - 列名也可能包含中文（如 `代销商`, `产品`, `价格`, `月份`）
   - SQL 生成时需要使用反引号包裹：`` `表名` ``, `` `列名` ``

3. **数据类型差异**：
   - MySQL 的 `datetime` 类型
   - `decimal` 类型用于精确数值
   - `char` 和 `varchar` 的区别

4. **NULL 值处理**：
   - MySQL 中 `IS NULL` 和 `IS NOT NULL` 的使用
   - 聚合函数对 NULL 的处理

5. **字符集**：
   - 确保使用 `utf8mb4` 字符集以支持中文

---

## 测试覆盖范围

- ✅ 基础 SELECT 查询
- ✅ WHERE 条件查询
- ✅ ORDER BY 排序
- ✅ LIMIT 分页
- ✅ 聚合函数（COUNT, SUM, AVG, MAX, MIN）
- ✅ GROUP BY 分组
- ✅ HAVING 过滤
- ✅ JOIN 连接查询（INNER, LEFT）
- ✅ 子查询（标量、IN、EXISTS）
- ✅ 日期时间函数
- ✅ 字符串函数
- ✅ CASE WHEN 条件表达式
- ✅ UNION 联合查询
- ✅ 窗口函数（MySQL 8.0+）
- ✅ 复杂业务场景查询
- ✅ NULL 值处理
- ✅ DISTINCT 去重

---

## 预期测试结果

每个测试用例应该：
1. **成功生成 SQL**：LLM 能够根据自然语言生成正确的 MySQL SQL
2. **SQL 语法正确**：生成的 SQL 符合 MySQL 语法规范
3. **结果正确**：执行 SQL 后返回的结果符合查询意图
4. **性能合理**：查询执行时间在可接受范围内

---

## 更新日志

- **2026-01-XX**: 初始版本，基于 chapter1 和 sql_homework 数据库结构创建测试用例

