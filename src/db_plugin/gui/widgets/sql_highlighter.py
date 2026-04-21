from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import QRegularExpression

# SQL keywords
SQL_KEYWORDS = [
    "SELECT", "FROM", "WHERE", "INSERT", "INTO", "UPDATE", "SET", "DELETE",
    "CREATE", "DROP", "ALTER", "TABLE", "INDEX", "VIEW", "SCHEMA",
    "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "ON", "CROSS",
    "AND", "OR", "NOT", "IN", "LIKE", "BETWEEN", "IS", "NULL",
    "AS", "ORDER", "BY", "GROUP", "HAVING", "LIMIT", "OFFSET",
    "DISTINCT", "ALL", "UNION", "EXISTS", "CASE", "WHEN", "THEN", "ELSE", "END",
    "PRIMARY", "KEY", "FOREIGN", "REFERENCES", "CONSTRAINT", "DEFAULT",
    "VALUES", "INT", "VARCHAR", "TEXT", "INTEGER", "BOOLEAN", "DATE",
    "TIMESTAMP", "FLOAT", "DOUBLE", "DECIMAL", "CHAR", "BIGINT", "SMALLINT",
    "SERIAL", "TRUE", "FALSE", "COUNT", "SUM", "AVG", "MAX", "MIN",
    "BEGIN", "COMMIT", "ROLLBACK", "TRANSACTION",
]

# SQL functions
SQL_FUNCTIONS = [
    "COALESCE", "CAST", "CONCAT", "SUBSTRING", "LENGTH", "UPPER", "LOWER",
    "TRIM", "NOW", "CURRENT_DATE", "CURRENT_TIME", "CURRENT_TIMESTAMP",
    "ABS", "ROUND", "CEIL", "FLOOR", "MOD", "POWER", "SQRT",
]


class SqlHighlighter(QSyntaxHighlighter):
    """SQL syntax highlighter for QTextEdit."""

    def __init__(self, document):
        super().__init__(document)

        self._keyword_format = QTextCharFormat()
        self._keyword_format.setForeground(QColor("#4A90D9"))
        self._keyword_format.setFontWeight(QFont.Bold)

        self._function_format = QTextCharFormat()
        self._function_format.setForeground(QColor("#9B59B6"))
        self._function_format.setFontWeight(QFont.Bold)

        self._string_format = QTextCharFormat()
        self._string_format.setForeground(QColor("#27AE60"))

        self._comment_format = QTextCharFormat()
        self._comment_format.setForeground(QColor("#95A5A6"))
        self._comment_format.setFontItalic(True)

        self._number_format = QTextCharFormat()
        self._number_format.setForeground(QColor("#E67E22"))

        self._keywords = set(SQL_KEYWORDS)
        self._functions = set(SQL_FUNCTIONS)
        self._keyword_pattern = QRegularExpression(
            r"\b(" + "|".join(self._keywords) + r")\b",
            QRegularExpression.PatternOption.CaseInsensitiveOption,
        )
        self._function_pattern = QRegularExpression(
            r"\b(" + "|".join(self._functions) + r")\b",
            QRegularExpression.PatternOption.CaseInsensitiveOption,
        )
        self._single_line_comment = QRegularExpression(r"--[^\n]*")
        self._multi_line_comment_start = QRegularExpression(r"/\*")
        self._multi_line_comment_end = QRegularExpression(r"\*/")
        self._string_single = QRegularExpression(r"'[^']*'")
        self._string_double = QRegularExpression(r'"[^"]*"')
        self._number = QRegularExpression(r"\b\d+(\.\d+)?\b")

    def highlightBlock(self, text):
        # Multi-line comments
        self._highlight_multiline_comments(text)

        # Single-line comments
        self._highlight_pattern(self._single_line_comment, text, self._comment_format)

        # Strings
        self._highlight_pattern(self._string_single, text, self._string_format)
        self._highlight_pattern(self._string_double, text, self._string_format)

        # Keywords
        self._highlight_pattern(self._keyword_pattern, text, self._keyword_format)

        # Functions
        self._highlight_pattern(self._function_pattern, text, self._function_format)

        # Numbers
        self._highlight_pattern(self._number, text, self._number_format)

    def _highlight_pattern(self, pattern, text, fmt):
        it = pattern.globalMatch(text)
        while it.hasNext():
            match = it.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

    def _highlight_multiline_comments(self, text):
        """Handle /* ... */ multi-line comments."""
        start_index = 0
        prev_state = self.previousBlockState()

        if prev_state == 1:
            end_match = self._multi_line_comment_end.match(text)
            if end_match.hasMatch():
                end_pos = end_match.capturedEnd()
                self.setFormat(0, end_pos, self._comment_format)
                start_index = end_pos
                self.setCurrentBlockState(0)
            else:
                self.setFormat(0, len(text), self._comment_format)
                self.setCurrentBlockState(1)
                return

        while start_index < len(text):
            start_match = self._multi_line_comment_start.match(text, start_index)
            if not start_match.hasMatch():
                break

            start_pos = start_match.capturedStart()
            end_match = self._multi_line_comment_end.match(text, start_pos + 2)
            if end_match.hasMatch():
                end_pos = end_match.capturedEnd()
                self.setFormat(start_pos, end_pos - start_pos, self._comment_format)
                start_index = end_pos
            else:
                self.setFormat(start_pos, len(text) - start_pos, self._comment_format)
                self.setCurrentBlockState(1)
                break
