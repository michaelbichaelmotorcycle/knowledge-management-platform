from unittest.mock import MagicMock, patch

from app.services.pdf_extraction import extract_text_from_pdf


def test_extract_text_from_pdf_combines_page_text():
    page_one = MagicMock()
    page_one.extract_text.return_value = "First page."

    page_two = MagicMock()
    page_two.extract_text.return_value = "Second page."

    mock_reader = MagicMock()
    mock_reader.pages = [page_one, page_two]

    with patch(
        "app.services.pdf_extraction.PdfReader",
        return_value=mock_reader,
    ):
        result = extract_text_from_pdf(b"fake-pdf")

    assert result == "First page.\n\nSecond page."


def test_extract_text_from_pdf_skips_pages_without_text():
    page_one = MagicMock()
    page_one.extract_text.return_value = "First page."

    page_two = MagicMock()
    page_two.extract_text.return_value = None

    page_three = MagicMock()
    page_three.extract_text.return_value = "Third page."

    mock_reader = MagicMock()
    mock_reader.pages = [page_one, page_two, page_three]

    with patch(
        "app.services.pdf_extraction.PdfReader",
        return_value=mock_reader,
    ):
        result = extract_text_from_pdf(b"fake-pdf")

    assert result == "First page.\n\nThird page."


def test_extract_text_from_pdf_returns_empty_string_for_empty_pdf():
    mock_reader = MagicMock()
    mock_reader.pages = []

    with patch(
        "app.services.pdf_extraction.PdfReader",
        return_value=mock_reader,
    ):
        result = extract_text_from_pdf(b"fake-pdf")

    assert result == ""
