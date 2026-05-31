"""
transcript.py — Script A
Fetches the transcript from a YouTube video URL or video ID.
"""

import re
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound


def extract_video_id(url_or_id: str) -> str:
    """Extract the YouTube video ID from a URL or return as-is if already an ID."""
    # Match standard, short, and embed URLs
    patterns = [
        r"(?:v=)([a-zA-Z0-9_-]{11})",          # ?v=VIDEO_ID
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",    # youtu.be/VIDEO_ID
        r"(?:embed/)([a-zA-Z0-9_-]{11})",         # /embed/VIDEO_ID
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    # Assume it's already a raw video ID
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url_or_id.strip()):
        return url_or_id.strip()
    raise ValueError(f"Could not extract a valid video ID from: {url_or_id}")


def get_transcript(url_or_id: str, language: str = "en") -> str:
    """
    Fetch the transcript for a YouTube video.

    Args:
        url_or_id: YouTube URL or video ID.
        language: Preferred language code (default 'en').

    Returns:
        The full transcript as a single string.

    Raises:
        ValueError: If no transcript is available.
    """
    video_id = extract_video_id(url_or_id)

    try:
        transcript_list = YouTubeTranscriptApi().list(video_id)

        # Try manual captions first, then auto-generated
        try:
            transcript = transcript_list.find_transcript([language])
        except NoTranscriptFound:
            # Fall back to any available language and translate
            transcript = transcript_list.find_transcript(
                transcript_list._manually_created_transcripts
                or transcript_list._generated_transcripts
            )

        segments = transcript.fetch()
        full_text = " ".join(seg.text for seg in segments)
        return full_text

    except TranscriptsDisabled:
        raise ValueError("Transcripts are disabled for this video.")
    except NoTranscriptFound:
        raise ValueError("No transcript found for this video in any language.")
    except Exception as e:
        raise ValueError(f"Failed to fetch transcript: {e}")


# ── Standalone test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_url = input("Paste a YouTube URL or video ID: ").strip()
    try:
        text = get_transcript(test_url)
        print(f"\n✅ Transcript fetched! Total characters: {len(text)}")
        print("\nFirst 500 characters:\n")
        print(text[:500])
    except ValueError as e:
        print(f"\n❌ Error: {e}")
