"""测试 pg-mcp 服务器功能"""

import asyncio
import json
from pg_mcp.server import mcp, app_lifespan


async def test_mcp():
    """运行 MCP 功能测试"""
    print("=" * 60)
    print("pg-mcp 功能测试")
    print("=" * 60)

    # 启动 lifespan
    print("\n[1] 初始化服务...")
    async with app_lifespan(mcp):
        print("[OK] 服务初始化成功")

        # 测试 list_databases
        print("\n[2] 测试 list_databases...")
        from pg_mcp.server import db_pool

        dbs = db_pool.list_databases()
        print(f"[OK] 可用数据库: {dbs}")

        # 测试 list_tables
        print("\n[3] 测试 list_tables (small 数据库)...")
        from pg_mcp.server import schema_service

        db_info = schema_service.get_cached("small")
        if db_info:
            schema_info = db_info.schemas.get("public")
            if schema_info:
                tables = list(schema_info.tables.keys())
                print(f"[OK] 表列表: {tables}")
            else:
                print("[FAIL] 未找到 public schema")
        else:
            print("[FAIL] 未找到 small 数据库缓存")

        # 测试 query (仅生成 SQL，不执行)
        print("\n[4] 测试 query (生成 SQL)...")
        from pg_mcp.server import query_service
        from pg_mcp.models.query import QueryRequest

        test_queries = [
            "列出所有用户",
            "统计每个订单的商品数量",
            "查找金额最高的订单",
        ]

        for q in test_queries:
            print(f"\n  问题: {q}")
            try:
                request = QueryRequest(
                    query=q,
                    database="small",
                    schema="public",
                    return_type="sql",  # 只生成SQL不执行
                    max_rows=10,
                )
                response = await query_service.execute_query(request)
                if response.success and response.data:
                    print(f"  生成SQL: {response.data.sql}")
                    if hasattr(response.data, 'explanation'):
                        print(f"  说明: {response.data.explanation}")
                if response.error:
                    print(f"  错误: {response.error.message}")
            except Exception as e:
                print(f"  错误: {e}")

        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_mcp())

