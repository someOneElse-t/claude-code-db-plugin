import csv
import json
import logging
from pathlib import Path

import openpyxl

from db_plugin.core.executor import QueryExecutor
from db_plugin.models.result import QueryResult

logger = logging.getLogger(__name__)


class ImportExportService:
    """Import and export data to/from CSV, Excel, and JSON."""

    def __init__(self, executor: QueryExecutor):
        self.executor = executor

    def export_csv(self, result: QueryResult, filepath: str) -> None:
        logger.info("Exporting %d rows to CSV: %s", result.row_count, filepath)
        path = Path(filepath)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=result.columns)
            writer.writeheader()
            for row in result.rows:
                writer.writerow(row)
        logger.info("CSV export complete")

    def export_excel(self, result: QueryResult, filepath: str) -> None:
        logger.info("Exporting %d rows to Excel: %s", result.row_count, filepath)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Query Result"
        ws.append(result.columns)
        for row in result.rows:
            ws.append([row.get(col) for col in result.columns])
        wb.save(filepath)
        logger.info("Excel export complete")

    def export_json(self, result: QueryResult, filepath: str) -> None:
        logger.info("Exporting %d rows to JSON: %s", result.row_count, filepath)
        path = Path(filepath)
        path.write_text(json.dumps(result.rows, indent=2, default=str), encoding="utf-8")
        logger.info("JSON export complete")

    def import_csv(self, filepath: str, table: str) -> int:
        logger.info("Importing CSV %s into table '%s'", filepath, table)
        dialect = self.executor.connection.get_dialect()
        path = Path(filepath)
        inserted = 0
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                result = dialect.insert(table, dict(row))
                if result.error_message is None:
                    inserted += 1
                else:
                    logger.warning("Failed to import row into '%s': %s", table, result.error_message)
        logger.info("CSV import complete: %d rows inserted into '%s'", inserted, table)
        return inserted

    def import_excel(self, filepath: str, table: str) -> int:
        logger.info("Importing Excel %s into table '%s'", filepath, table)
        dialect = self.executor.connection.get_dialect()
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        headers = [cell.value for cell in ws[1]]
        inserted = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            data = dict(zip(headers, row))
            result = dialect.insert(table, data)
            if result.error_message is None:
                inserted += 1
            else:
                logger.warning("Failed to import row into '%s': %s", table, result.error_message)
        logger.info("Excel import complete: %d rows inserted into '%s'", inserted, table)
        return inserted
