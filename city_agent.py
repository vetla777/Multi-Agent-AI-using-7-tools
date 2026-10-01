import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich import print
from rich.panel import Panel
from rich.console import Console
from agents import build_city_agent

console = Console()

def main():
    console.print(
        Panel.fit(
            "[bold cyan]🏙️ Multi-Tool City & Intelligence Agent[/bold cyan]\n"
            "[dim]Equipped with Weather, News, Places, Wikipedia, Math, and Web Search[/dim]\n"
            "[yellow]Human Approval is enabled for all tool calls.[/yellow]\n"
            "[green]Type 'exit' or 'quit' to end session.[/green]",
            border_style="cyan"
        )
    )

    # Initialize city agent with human approval middleware
    agent = build_city_agent(enable_human_approval=True)

    chat_history = []

    while True:
        try:
            user_input = input("\nYou : ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("\n[bold green]Goodbye! 👋[/bold green]\n")
                break

            chat_history.append({"role": "user", "content": user_input})

            with console.status("[bold green]Agent is thinking & selecting tools...", spinner="dots"):
                result = agent.invoke({
                    "messages": chat_history
                })

            raw_reply = result["messages"][-1].content
            if isinstance(raw_reply, list):
                bot_reply = "".join(
                    c.get("text", "") if isinstance(c, dict) else str(c) for c in raw_reply
                )
            else:
                bot_reply = str(raw_reply)

            chat_history.append({"role": "assistant", "content": bot_reply})

            print(f"\n[bold magenta]Bot :[/bold magenta]\n{bot_reply}")

        except KeyboardInterrupt:
            print("\n[yellow]Session terminated by user.[/yellow]")
            break
        except Exception as e:
            print(f"\n[bold red]Error:[/bold red] {str(e)}")

if __name__ == "__main__":
    main()
