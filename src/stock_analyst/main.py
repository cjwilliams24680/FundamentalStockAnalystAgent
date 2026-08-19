import asyncio

from stock_analyst.orchestrator import run_orchestrator


async def main():
    await run_orchestrator()

def run() -> None:
    asyncio.run(main())

if __name__ == "__main__":
    run()
