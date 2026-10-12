"""Chat with the bot in the terminal.

    python -m rag_bot.chat            # normal chat
    python -m rag_bot.chat --debug    # also shows the distance and whether the LLM was called
"""
import argparse

from rag_bot.bot import SupportBot


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat with the VoltEdge support bot.")
    parser.add_argument("--debug", action="store_true", help="show distance and LLM usage")
    args = parser.parse_args()

    print("Loading the knowledge base ...")
    bot = SupportBot.from_disk()
    print("VoltEdge support bot ready. Type your question (or 'exit').\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question.lower() in {"exit", "quit"}:
            break
        answer = bot.ask(question)
        print(f"\nBot: {answer.text}")
        for source in answer.sources:
            print(f"   Source: {source.label}")
        if args.debug and answer.top_distance is not None:
            print(f"   [distance {answer.top_distance:.3f} | LLM {'called' if answer.used_llm else 'not called'}]")
        print()


if __name__ == "__main__":
    main()
