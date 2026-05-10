import pandas as pd
from pathlib import Path
from fastmcp import FastMCP

CSV_PATH = Path(__file__).parent / "inventory.csv"

mcp = FastMCP("Inventory Manager")


def _load() -> pd.DataFrame:
    return pd.read_csv(CSV_PATH)


def _save(df: pd.DataFrame) -> None:
    df.to_csv(CSV_PATH, index=False)


@mcp.tool()
def check_stock(item_name: str) -> str:
    """Return the current stock level and price for an item."""
    df = _load()
    match = df[df["item_name"].str.lower() == item_name.lower()]
    if match.empty:
        return f"Item '{item_name}' not found in inventory."
    row = match.iloc[0]
    return (
        f"Item: {row['item_name']}\n"
        f"Price: ${row['price']:.2f}\n"
        f"Stock level: {int(row['stock_level'])} units"
    )


@mcp.tool()
def process_sale(item_name: str, quantity: int) -> str:
    """Reduce stock for an item after a sale. Returns updated stock level."""
    if quantity <= 0:
        return "Quantity must be a positive integer."

    df = _load()
    mask = df["item_name"].str.lower() == item_name.lower()
    if not mask.any():
        return f"Item '{item_name}' not found in inventory."

    idx = df[mask].index[0]
    current = int(df.at[idx, "stock_level"])

    if quantity > current:
        return (
            f"Cannot process sale: only {current} units of "
            f"'{df.at[idx, 'item_name']}' in stock (requested {quantity})."
        )

    df.at[idx, "stock_level"] = current - quantity
    _save(df)

    new_level = int(df.at[idx, "stock_level"])
    return (
        f"Sale recorded: {quantity} x {df.at[idx, 'item_name']}.\n"
        f"Stock updated: {current} → {new_level} units."
    )


@mcp.resource("inventory://daily-report")
def daily_report() -> str:
    """Full inventory as a Markdown table for the daily report."""
    df = _load()
    df["price"] = df["price"].apply(lambda p: f"${p:.2f}")
    df.columns = ["Item Name", "Price", "Stock Level"]

    col_widths = [
        max(len(str(v)) for v in [col] + df[col].tolist())
        for col in df.columns
    ]

    def _row(values):
        return "| " + " | ".join(str(v).ljust(w) for v, w in zip(values, col_widths)) + " |"

    separator = "| " + " | ".join("-" * w for w in col_widths) + " |"

    lines = [
        "# Daily Inventory Report",
        "",
        _row(df.columns),
        separator,
        *[_row(row) for row in df.itertuples(index=False)],
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
