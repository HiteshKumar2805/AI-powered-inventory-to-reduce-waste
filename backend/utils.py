# utils.py
import pandas as pd
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"sku", "date", "sales", "inventory", "expiry_date"}


def parse_csv(file_obj: BytesIO) -> pd.DataFrame:
    """
    Parses uploaded CSV file and ensures required columns exist.
    Also converts date fields to datetime.
    """
    try:
        df = pd.read_csv(file_obj)

        # Normalize column names
        df.columns = [col.strip().lower() for col in df.columns]

        # Check for required columns
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Convert date columns
        for col in ['date', 'expiry_date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Sort for consistency
        df = df.sort_values(by=["sku", "date"])

        logger.info("CSV parsed successfully.")
        return df

    except Exception as e:
        logger.error(f"Failed to parse CSV: {e}")
        raise ValueError(f"Failed to parse CSV: {e}")


def load_inventory_data(filepath: str = "backend/inventory_data.csv") -> pd.DataFrame:
    """
    Loads inventory data from local CSV (useful for testing/debugging).
    Ensures datetime parsing and sorting.
    """
    try:
        with open(filepath, 'rb') as f:
            return parse_csv(f)
    except Exception as e:
        logger.error(f"Error loading inventory data: {e}")
        raise e
