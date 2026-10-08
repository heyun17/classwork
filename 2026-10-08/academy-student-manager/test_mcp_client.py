import asyncio

from mcp import Client


async def main() -> None:
    async with Client(
        "http://127.0.0.1:8001/mcp"
    ) as client:

        tools = await client.list_tools()

        print("=== MCP Tools ===")

        for tool in tools.tools:
            print(tool.name)

        dashboard = await client.call_tool(
            "get_dashboard",
            {},
        )

        print("\n=== get_dashboard 결과 ===")
        print(dashboard.structured_content)
        print("is_error:", dashboard.is_error)

        student = await client.call_tool(
            "get_student_detail",
            {
                "student_id": 1,
            },
        )

        print("\n=== get_student_detail 결과 ===")
        print(student.structured_content)
        print("is_error:", student.is_error)


asyncio.run(main())