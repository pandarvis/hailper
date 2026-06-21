from hailper.mail import parse_email_message

PLAIN = (
    b"From: EDF <contact@edf.fr>\r\n"
    b"Subject: Votre facture\r\n"
    b"Date: Fri, 20 Jun 2026 09:00:00 +0200\r\n"
    b"Content-Type: text/plain; charset=utf-8\r\n"
    b"\r\n"
    b"Bonjour, votre facture est disponible.\r\n"
)

HTML = (
    b"From: Orange <no-reply@orange.fr>\r\n"
    b"Subject: =?UTF-8?B?T2ZmcmU=?=\r\n"
    b"Date: Fri, 20 Jun 2026 10:00:00 +0200\r\n"
    b"Content-Type: text/html; charset=utf-8\r\n"
    b"\r\n"
    b"<html><body><p>Bonjour</p><p>Nouvelle offre</p></body></html>\r\n"
)

def test_parse_plain():
    e = parse_email_message(PLAIN, index=1)
    assert e.index == 1
    assert "EDF" in e.sender
    assert e.subject == "Votre facture"
    assert "facture est disponible" in e.body

def test_parse_html_is_stripped():
    e = parse_email_message(HTML, index=2)
    assert e.subject == "Offre"  # decoded MIME header
    assert "<" not in e.body
    assert "Bonjour" in e.body and "Nouvelle offre" in e.body
