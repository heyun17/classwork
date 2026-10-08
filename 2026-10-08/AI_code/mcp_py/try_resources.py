import asyncio

from mcp import Client

from sales_server import mcp


async def main() -> None:
    async with Client(mcp) as client:
        print([r.uri for r in (await client.list_resources()).resources])
        print([t.uri_template for t in (await client.list_resource_templates()).resource_templates])

        r = await client.read_resource("sales://region/서울")
        print(r.contents[0].text)

        prompts = await client.list_prompts()
        print([(p.name, [a.name for a in p.arguments]) for p in prompts.prompts])
        p = await client.get_prompt("sales_report", {"region": "부산"})
        print(p.messages[0].content.text)


asyncio.run(main())