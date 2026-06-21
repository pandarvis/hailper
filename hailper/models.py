from dataclasses import dataclass


@dataclass
class Track:
    title: str
    video_id: str
    added_at: str = ""


@dataclass
class Email:
    index: int
    sender: str
    subject: str
    date: str
    body: str
