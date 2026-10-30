"""Generate the placeholder app icon (256x256 PNG) used by the AppImage."""
import sys

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QLinearGradient, QPainter

app = QGuiApplication([])
img = QImage(256, 256, QImage.Format_ARGB32)
img.fill(Qt.transparent)
p = QPainter(img)
p.setRenderHint(QPainter.Antialiasing)
g = QLinearGradient(0, 0, 256, 256)
g.setColorAt(0, QColor("#3b82f6"))
g.setColorAt(1, QColor("#1e3a8a"))
p.setBrush(g)
p.setPen(Qt.NoPen)
p.drawRoundedRect(QRectF(16, 16, 224, 224), 48, 48)
p.setPen(QColor("white"))
f = QFont("Sans")
f.setBold(True)
f.setPixelSize(104)
p.setFont(f)
p.drawText(QRectF(16, 16, 224, 224), Qt.AlignCenter, "MKV")
p.end()
img.save(sys.argv[1])
