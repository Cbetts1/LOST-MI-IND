"""
AIRepl: An interactive REPL for VAI-OS that forwards user input to the
AI engine and formats responses for display.
"""
import logging

logger = logging.getLogger(__name__)


class AIRepl:
    """Interactive REPL backed by the VAI-OS AI engine."""

    def __init__(self, ai_engine):
        self._engine = ai_engine
        self._history: list[str] = []
        logger.info("AIRepl initialized")

    def _format_response(self, r: dict) -> str:
        """Format an AI inference response dict for display."""
        if not r:
            return "(no response)"
        response = r.get("response", "")
        confidence = r.get("confidence", 0.0)
        tokens = r.get("tokens", 0)
        return (
            f"{response}\n"
            f"  [confidence={confidence:.2f} tokens={tokens}]"
        )

    def run(self) -> None:
        """
        Start the AI REPL loop.

        Accepts user input, forwards to AI engine, and prints formatted
        responses. Handles Ctrl+C to continue and Ctrl+D / 'quit' to exit.
        """
        print("VAI-OS AI REPL  (type 'quit' or Ctrl+D to exit)")
        print("=" * 50)
        while True:
            try:
                prompt = input("ai> ").strip()
            except KeyboardInterrupt:
                print()
                continue
            except EOFError:
                print("\nExiting AI REPL.")
                break
            if not prompt:
                continue
            if prompt.lower() in ("quit", "exit", "q"):
                print("Exiting AI REPL.")
                break
            self._history.append(prompt)
            try:
                result = self._engine.infer(
                    "default", prompt, {"history": self._history[-5:]}
                )
                print(self._format_response(result))
            except Exception as exc:
                logger.error("AI REPL inference error: %s", exc)
                print(f"Error: {exc}")
