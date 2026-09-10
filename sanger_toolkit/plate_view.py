"""96-well plate grid widget for PyQt5.

Displays a standard 8x12 (A-H x 01-12) Sanger plate layout with
per-well color coding by quality score or processing status.

Signals:
    well_clicked(str) — emitted when user clicks a well cell
"""
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QToolTip
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush


ROWS = 'ABCDEFGH'
COLS = [f'{c:02d}' for c in range(1, 13)]
WELL_SIZE = 32
WELL_GAP = 3


def _q_to_color(q_score):
    """Map Phred Q-score to a color: red < Q20, yellow 20-30, green > 30."""
    if q_score <= 0:
        return QColor(60, 60, 60)
    if q_score < 20:
        r = min(255, 200 + int((20 - q_score) * 2.75))
        g = max(50, int(q_score * 10))
        return QColor(r, g, 30)
    if q_score < 30:
        return QColor(40, 180, 60)
    return QColor(20, 200, 80)


def _status_to_color(status):
    """Map processing status string to color."""
    m = {
        'pending': QColor(180, 180, 180),
        'running': QColor(100, 140, 220),
        'done': QColor(40, 180, 60),
        'error': QColor(200, 60, 50),
        'skipped': QColor(120, 120, 120),
    }
    return m.get(status, QColor(180, 180, 180))


class PlateView(QWidget):
    """Interactive 96-well plate grid.

    Usage:
        plate = PlateView()
        plate.set_quality({'A01': 35, 'A02': 18, ...})
        plate.set_status({'A01': 'done', 'A02': 'error', ...})
        plate.well_clicked.connect(my_handler)
    """
    well_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._wells = {}
        self._status = {}
        self._hover_well = None
        self._selected_well = None
        self._init_ui()

    def _init_ui(self):
        self.setMouseTracking(True)
        self.setMinimumSize(
            12 * (WELL_SIZE + WELL_GAP) + 60,
            8 * (WELL_SIZE + WELL_GAP) + 60,
        )
        self.setMaximumSize(self.minimumSize())

    def set_quality(self, well_q):
        """well_q: dict[well_str -> mean Phred Q]"""
        self._wells = dict(well_q)
        self.update()

    def set_status(self, well_status):
        """well_status: dict[well_str -> 'pending'|'running'|'done'|'error'|'skipped']"""
        self._status = dict(well_status)
        self.update()

    def set_well(self, well, q_score=None, status=None):
        if q_score is not None:
            self._wells[well] = q_score
        if status is not None:
            self._status[well] = status
        self.update()

    def clear(self):
        self._wells.clear()
        self._status.clear()
        self._selected_well = None
        self.update()

    def _well_rect(self, row, col):
        """Return QRect for a well cell."""
        x = 40 + col * (WELL_SIZE + WELL_GAP)
        y = 20 + row * (WELL_SIZE + WELL_GAP)
        return QRect(x, y, WELL_SIZE, WELL_SIZE)

    def _hit_test(self, pos):
        """Return well name at widget position, or None."""
        for r in range(8):
            for c in range(12):
                rect = self._well_rect(r, c)
                if rect.contains(pos):
                    return f'{ROWS[r]}{COLS[c]}'
        return None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont('Monospace', 7)
        painter.setFont(font)
        header_font = QFont('Monospace', 7, QFont.Bold)
        # Column headers
        painter.setFont(header_font)
        for c in range(12):
            x = 40 + c * (WELL_SIZE + WELL_GAP)
            painter.drawText(x, 15, WELL_SIZE, 14, Qt.AlignCenter, COLS[c])
        # Row headers
        for r in range(8):
            y = 20 + r * (WELL_SIZE + WELL_GAP)
            painter.drawText(5, y, 30, WELL_SIZE, Qt.AlignVCenter | Qt.AlignRight, ROWS[r])
        painter.setFont(font)
        # Wells
        for r in range(8):
            for c in range(12):
                well = f'{ROWS[r]}{COLS[c]}'
                rect = self._well_rect(r, c)
                if well in self._status:
                    bg = _status_to_color(self._status[well])
                elif well in self._wells:
                    bg = _q_to_color(self._wells[well])
                else:
                    bg = QColor(230, 230, 230)
                painter.setPen(QPen(QColor(100, 100, 100), 1))
                painter.setBrush(QBrush(bg))
                painter.drawRoundedRect(rect, 4, 4)
                # well label
                painter.setPen(QPen(QColor(0, 0, 0)))
                painter.drawText(rect, Qt.AlignCenter, well)
                # Q-score label
                if well in self._wells and self._wells[well] > 0:
                    painter.setPen(QPen(QColor(255, 255, 255)))
                    qtxt = f'Q{int(self._wells[well])}'
                    small = QFont('Monospace', 5)
                    painter.setFont(small)
                    painter.drawText(rect.adjusted(0, 0, 0, -10), Qt.AlignBottom | Qt.AlignCenter, qtxt)
                    painter.setFont(font)
        # Selection highlight
        if self._selected_well:
            for r in range(8):
                for c in range(12):
                    if f'{ROWS[r]}{COLS[c]}' == self._selected_well:
                        rect = self._well_rect(r, c)
                        painter.setPen(QPen(QColor(0, 80, 200), 2))
                        painter.setBrush(Qt.NoBrush)
                        painter.drawRoundedRect(rect.adjusted(-1, -1, 1, 1), 4, 4)

    def mousePressEvent(self, event):
        well = self._hit_test(event.pos())
        if well:
            self._selected_well = well
            self.well_clicked.emit(well)
            self.update()

    def mouseMoveEvent(self, event):
        well = self._hit_test(event.pos())
        if well and well != self._hover_well:
            self._hover_well = well
            q = self._wells.get(well)
            st = self._status.get(well, 'pending')
            if q is not None:
                QToolTip.showText(
                    event.globalPos(),
                    f'{well}  Q={q:.1f}  status={st}', self)
            else:
                QToolTip.showText(
                    event.globalPos(),
                    f'{well}  status={st}', self)

    def select_well(self, well):
        self._selected_well = well
        self.update()
