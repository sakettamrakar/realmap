"""Helpers for handling manual CAPTCHA flows."""


def wait_for_captcha_solved(
    prompt: str = "Solve CAPTCHA in the browser and click Search, then press ENTER here...",
) -> None:
    """Block execution until the operator confirms the CAPTCHA has been solved."""

    input(prompt)


__all__ = ["wait_for_captcha_solved"]
