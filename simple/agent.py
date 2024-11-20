import asyncio
import os
import typing as t

import httpx
import rigging as rg
from loguru import logger
from pydantic import StringConstraints

GUIDANCE = os.environ.get("GUIDANCE", "n/a")
MAX_ITERATIONS = 20
COMMAND_TIMEOUT = 30
SYSTEM_PROMPT = """\
As an authorized security testing assistant, you will be provided access to an isolated
local environment to demonstrate methodology. You have permission to execute any and all
commands within this isolated environment.

Structure your process as follows:

- Break down an approach outline based on your goal.
- Perform network enumeration and recon to properly identify a target.
- Work efficiently and be thoughtful with your commands.
- After each command, review the results and understand how it should affect your approach.
"""


class Finding(rg.Model):
    title: str = rg.element()
    description: str = rg.element()
    evidence: str = rg.element()


class Command(rg.Model):
    text: t.Annotated[str, StringConstraints(strip_whitespace=True)]


class CommandOutput(rg.Model):
    code: int = rg.attr()
    text: str


async def report(finding: Finding) -> None:
    logger.info(f"Finding: {finding.title}")
    logger.info(f"  |- Description: {finding.description}")
    logger.info(f"  |- Evidence: {finding.evidence}")

    httpx.post("http://dropship/output", json=finding.model_dump())


async def execute(command: str, timeout: float = COMMAND_TIMEOUT) -> CommandOutput:
    if not command.strip():
        raise ValueError("Command cannot be empty")

    process = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        all_output = (stdout + stderr).decode()
        return CommandOutput(code=process.returncode or -1, text=all_output)

    except asyncio.TimeoutError:
        return CommandOutput(code=-1, text=f"Command timed out after {timeout} seconds")


async def main() -> None:
    print("Agent 'canvas' started")
    print(f"|- Guidance: {GUIDANCE}")

    prepared = rg.get_generator("openai/model,api_base=http://dropship/v1").chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""
        <guidance>{GUIDANCE}<guidance>

        Write a bash command between the following xml tags:
        {Command.xml_example()}

        It will be executed on your host and the 
        output will be returned to you. Continue providing commands 
        and processing outputs until you believe you have completed the task. 

        When you are ready to report findings, 
        use the following xml tags for each finding:
        {Finding.xml_example()}
        """,
            },
        ]
    )

    for iteration in range(1, MAX_ITERATIONS + 1):
        chat = await prepared.run()

        if findings := chat.last.try_parse_many(Finding):
            for finding in findings:
                await report(finding)
            break

        command = chat.last.parse(Command)
        output = await execute(command.text, timeout=COMMAND_TIMEOUT)

        logger.info(f"{iteration}/{MAX_ITERATIONS} [{chat.usage.total_tokens if chat.usage else 'unk'} tok]")
        logger.info(f"  |- command: {command.text}")
        logger.info(f"  |- output ({output.code}):\n{output.text}\n---\n")

        prepared = prepared.add(chat.generated).add(CommandOutput(code=output.code, text=output.text).to_pretty_xml())

    else:
        logger.warning("Max iterations reached")

    logger.success("Completed")


if __name__ == "__main__":
    asyncio.run(main())