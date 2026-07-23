# SPDX-License-Identifier: MIT
"""
pdf_processor.py -- PDF-Verarbeitungs-Service (STUB)

TODO: Implementierung extrahieren aus BACH tools/ oder neu implementieren.
      Moegliche Basis: PyMuPDF (fitz) fuer Textextraktion

Geplante Funktionen:
- extract_text(pdf_path) -> str
- extract_pages(pdf_path, pages=[]) -> list[str]
- pdf_to_images(pdf_path, dpi=150) -> list[PIL.Image]
- merge_pdfs(pdf_paths, output_path) -> bool

Dependencies:
    pip install PyMuPDF  (fuer fitz)
    pip install pypdf    (reines Python, kein C)
    pip install Pillow   (fuer Bildverarbeitung)

Referenz: BACH LESSON "PyMuPDF: Save-to-Original erfordert Temp-Datei"
"""


class PdfProcessor:
    """PDF-Verarbeitungs-Service -- STUB, noch nicht implementiert."""

    def __init__(self):
        self._backend = self._detect_backend()

    def _detect_backend(self) -> str:
        """Erkennt verfuegbares PDF-Backend."""
        try:
            import fitz  # noqa: F401

            return "pymupdf"
        except ImportError:
            pass
        try:
            import pypdf  # noqa: F401

            return "pypdf"
        except ImportError:
            pass
        return "none"

    def extract_text(self, pdf_path: str) -> str:
        """
        Extrahiert Text aus PDF-Datei.

        Args:
            pdf_path: Pfad zur PDF-Datei

        Returns:
            Extrahierter Text als String

        Raises:
            NotImplementedError: Noch nicht implementiert
            ImportError: Kein PDF-Backend verfuegbar
        """
        if self._backend == "none":
            raise ImportError(
                "Kein PDF-Backend gefunden. Installiere: pip install PyMuPDF"
            )
        # TODO: Implementierung
        raise NotImplementedError(
            "pdf_processor.extract_text() noch nicht implementiert"
        )

    def extract_pages(self, pdf_path: str, pages: list = None) -> list:
        """
        Extrahiert Text seitenweise aus PDF.

        Args:
            pdf_path: Pfad zur PDF-Datei
            pages:    Seitennummern (0-basiert), None = alle Seiten

        Returns:
            Liste von Strings (eine pro Seite)
        """
        raise NotImplementedError(
            "pdf_processor.extract_pages() noch nicht implementiert"
        )

    def get_info(self) -> dict:
        """Gibt Info ueber verfuegbares Backend zurueck."""
        return {
            "backend": self._backend,
            "status": "stub",
            "todo": "Implementierung aus BACH extrahieren",
        }
