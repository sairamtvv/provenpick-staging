"""
Cleanup script to remove archived items past retention period.
Run this periodically (e.g., via cron job).
"""

import asyncio
import os
from datetime import datetime
from backend.db.tables import ArchiveTable
from backend.db.connection import DB


async def cleanup_archives():
    """Remove archives past retention period"""

    print(f"Starting archive cleanup at {datetime.now()}")

    # Find expired items
    expired = (
        await ArchiveTable.select()
        .where(ArchiveTable.retention_until < datetime.now())
        .run()
    )

    print(f"Found {len(expired)} expired archives")

    if expired:
        # Delete expired
        await (
            ArchiveTable.delete()
            .where(ArchiveTable.retention_until < datetime.now())
            .run()
        )

        print(f"Deleted {len(expired)} expired archives")
    else:
        print("No expired archives to clean up")

    print(f"Cleanup completed at {datetime.now()}")


if __name__ == "__main__":
    asyncio.run(cleanup_archives())
