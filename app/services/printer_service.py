"""
Printer service.

Formats kitchen and bar receipts as fixed-width plain text suitable for
ESC/POS thermal printers (standard 42-character width).

In production this module would send the formatted text to a receipt
printer over USB/serial or stream it to a kitchen display system (KDS)
via WebSocket.  For now the receipt is returned as a string and logged.
"""

import logging

from app.schemas.menu_order_schema import KitchenBon

logger = logging.getLogger(__name__)

# Standard thermal printer width in characters
BON_WIDTH = 42


# ── Layout helpers ────────────────────────────────────────────────────────────

def _rule(char: str = "─") -> str:
    """Return a horizontal rule of BON_WIDTH characters."""
    return char * BON_WIDTH


def _center(text: str) -> str:
    """Centre text within BON_WIDTH characters."""
    return text.center(BON_WIDTH)


def _left_right(left: str, right: str) -> str:
    """Print *left* flush-left and *right* flush-right on the same line."""
    gap = BON_WIDTH - len(left) - len(right)
    return left + " " * max(1, gap) + right


# ── Public API ────────────────────────────────────────────────────────────────

def format_receipt(bon: KitchenBon) -> str:
    """
    Render a KitchenBon as a formatted receipt string.

    Example output (truncated):
        ══════════════════════════════════════════
                  BLOCKBRÄU HAMBURG
              Bei den St. Pauli Landungsbrücken 3
        ══════════════════════════════════════════
        BON: BON-0007-K              TYPE: KITCHEN
        ──────────────────────────────────────────
        Guest:   Maria Schmidt
        Seats:   4
        Code:    X4KR2A9MBQ
        Date:    09.03.2026
        Time:    14:32:05 UTC
        ──────────────────────────────────────────
        POS  QTY    ITEM
        ──────────────────────────────────────────
          1   1x    Pork knuckle (approx. 700 g)
          2   2x    Bratwurst (2 pcs)
        ──────────────────────────────────────────
        ! Special request: No mustard please
        ══════════════════════════════════════════
        Food:                        €  24.90
        Beverages:                   €   0.00
        TOTAL:                       €  24.90
        ══════════════════════════════════════════
    """
    lines: list[str] = []

    # ── Header ────────────────────────────────────────────────────────────────
    lines.append(_rule("═"))
    lines.append(_center("BLOCKBRÄU HAMBURG"))
    lines.append(_center("Bei den St. Pauli Landungsbrücken 3"))
    lines.append(_rule("═"))

    # ── Receipt metadata ──────────────────────────────────────────────────────
    lines.append(_left_right(f"BON: {bon.bon_number}", f"TYPE: {bon.bon_type}"))
    lines.append(_rule())

    # ── Guest information ─────────────────────────────────────────────────────
    lines.append(f"Guest:   {bon.guest_name}")
    lines.append(f"Seats:   {bon.table_seats}")
    lines.append(f"Code:    {bon.confirmation_code}")
    lines.append(f"Date:    {bon.fired_at.strftime('%d.%m.%Y')}")
    lines.append(f"Time:    {bon.fired_at.strftime('%H:%M:%S')} UTC")
    lines.append(_rule())

    # ── Item table ────────────────────────────────────────────────────────────
    lines.append(f"{'POS':<4} {'QTY':<6} ITEM")
    lines.append(_rule())

    for item in bon.items:
        lines.append(f"{item.position:<4} {str(item.quantity) + 'x':<6} {item.item_name}")
        if item.notes:
            # Indent note beneath the item name
            lines.append(f"           ↳ {item.notes}")

    lines.append(_rule())

    # ── Special requests ──────────────────────────────────────────────────────
    if bon.special_requests:
        lines.append(f"! Special request: {bon.special_requests}")
        lines.append(_rule())

    # ── Totals ────────────────────────────────────────────────────────────────
    lines.append(_rule("═"))
    lines.append(_left_right("Food:",      f"€ {bon.subtotal_food:>7.2f}"))
    lines.append(_left_right("Beverages:", f"€ {bon.subtotal_beverages:>7.2f}"))
    lines.append(_left_right("TOTAL:",     f"€ {bon.total_amount:>7.2f}"))
    lines.append(_rule("═"))

    return "\n".join(lines)


def print_receipt(bon: KitchenBon) -> str:
    """
    Format and 'print' a single receipt.

    Logs the formatted text at INFO level (replace with actual printer
    communication in production) and returns the text for the API response.

    Args:
        bon: The kitchen or bar receipt to print.

    Returns:
        The formatted receipt as a plain-text string.
    """
    text = format_receipt(bon)
    logger.info(
        "\n%s\n[PRINTER] Receipt %s sent.\n%s",
        "=" * BON_WIDTH,
        bon.bon_number,
        text,
    )
    return text


def print_both_receipts(
    kitchen_bon: KitchenBon | None,
    bar_bon:     KitchenBon | None,
) -> dict[str, str | None]:
    """
    Print the kitchen receipt and the bar receipt for one order.

    Either receipt may be None if the order contained no items for
    that station (e.g. food-only order has no bar receipt).

    Args:
        kitchen_bon: Kitchen receipt, or None.
        bar_bon:     Bar receipt, or None.

    Returns:
        Dictionary with keys 'kitchen_bon_text' and 'bar_bon_text'.
    """
    result: dict[str, str | None] = {
        "kitchen_bon_text": None,
        "bar_bon_text":     None,
    }

    if kitchen_bon:
        result["kitchen_bon_text"] = print_receipt(kitchen_bon)
        logger.info("Kitchen receipt %s printed.", kitchen_bon.bon_number)

    if bar_bon:
        result["bar_bon_text"] = print_receipt(bar_bon)
        logger.info("Bar receipt %s printed.", bar_bon.bon_number)

    if not kitchen_bon and not bar_bon:
        logger.info("No receipts to print (no pre-order).")

    return result