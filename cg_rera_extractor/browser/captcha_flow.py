"""Helpers for handling manual CAPTCHA flows."""

import logging
import sys
import time
import threading

LOGGER = logging.getLogger(__name__)


def wait_for_captcha_solved(
    prompt: str = "Solve CAPTCHA in the browser and click Search, then press ENTER here...",
) -> None:
    """Block execution until the operator confirms the CAPTCHA has been solved.
    
    Uses a thread to allow safe interruption without closing browser.
    """
    print(prompt)
    print("\n>>> Browser is waiting. Solve the CAPTCHA, click Search, then come back.")
    print(">>> Press ENTER in this terminal when the listings are visible...")
    
    # Use threading to implement a timeout without blocking hard
    user_input_received = False
    
    def wait_for_input():
        nonlocal user_input_received
        try:
            input("")
            user_input_received = True
        except (KeyboardInterrupt, EOFError):
            pass
    
    # Start input thread as daemon so it won't prevent exit
    input_thread = threading.Thread(target=wait_for_input, daemon=True)
    input_thread.start()
    
    max_wait_seconds = 300  # 5 minute timeout
    check_interval = 1.0
    elapsed = 0
    
    while elapsed < max_wait_seconds and not user_input_received:
        time.sleep(check_interval)
        elapsed += check_interval
        
        # Show progress every 30 seconds
        if int(elapsed) % 30 == 0:
            remaining = max_wait_seconds - int(elapsed)
            print(f"... still waiting ({int(elapsed)}s elapsed, {remaining}s remaining) ...")
    
    if user_input_received:
        LOGGER.info("User confirmed CAPTCHA solved")
    else:
        LOGGER.warning("CAPTCHA wait timeout after %d seconds", max_wait_seconds)
        print(f"\nTimeout after {max_wait_seconds} seconds. Proceeding anyway...")


__all__ = ["wait_for_captcha_solved"]
