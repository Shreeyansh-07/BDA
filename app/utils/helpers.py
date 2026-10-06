import base64
import urllib.parse
from typing import List, Optional

def format_rating_stars(rating: float) -> str:
    """Formats numeric rating (e.g. 4.2) into a star string."""
    try:
        val = float(rating)
        full_stars = int(val)
        has_half = (val - full_stars) >= 0.5
        stars = "★" * full_stars + ("½" if has_half else "")
        return f"{stars} ({val:.1f})"
    except Exception:
        return "★ N/A"

def format_runtime(runtime_str: str) -> str:
    """Formats runtime string e.g. '125 min' to '2h 5m'."""
    try:
        mins = int(str(runtime_str).replace("min", "").strip())
        hours = mins // 60
        remainder = mins % 60
        if hours > 0:
            return f"{hours}h {remainder}m"
        return f"{remainder}m"
    except Exception:
        return str(runtime_str)

def generate_svg_poster(title: str, year: str, genre: str = "Cinema") -> str:
    """
    Generates a crisp, cinematic gradient SVG poster data URL
    when TMDb poster image is missing or unavailable.
    """
    safe_title = title[:24] + "..." if len(title) > 24 else title
    safe_year = str(year)
    safe_genre = genre.split("|")[0] if "|" in genre else genre

    # Elegant cinematic SVG with gradient and typography
    svg_data = f"""<svg xmlns="http://www.w3.org/2000/svg" width="300" height="450" viewBox="0 0 300 450">
        <defs>
            <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#141e30" />
                <stop offset="50%" stop-color="#243b55" />
                <stop offset="100%" stop-color="#0f172a" />
            </linearGradient>
            <linearGradient id="gold" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#f59e0b" />
                <stop offset="100%" stop-color="#d97706" />
            </linearGradient>
        </defs>
        <rect width="300" height="450" fill="url(#grad)" rx="12" />
        <rect x="15" y="15" width="270" height="420" fill="none" stroke="#334155" stroke-width="1.5" rx="8" stroke-dasharray="4 4" />
        
        <circle cx="150" cy="160" r="50" fill="#1e293b" opacity="0.6" />
        <path d="M140 140 L170 160 L140 180 Z" fill="url(#gold)" />
        
        <text x="150" y="270" font-family="'Helvetica Neue', Arial, sans-serif" font-size="16" font-weight="bold" fill="#f8fafc" text-anchor="middle">
            {safe_title}
        </text>
        <text x="150" y="295" font-family="'Helvetica Neue', Arial, sans-serif" font-size="13" fill="#94a3b8" text-anchor="middle">
            {safe_year}
        </text>
        
        <rect x="90" y="320" width="120" height="24" fill="#e11d48" rx="12" opacity="0.9"/>
        <text x="150" y="336" font-family="'Helvetica Neue', Arial, sans-serif" font-size="11" font-weight="600" fill="#ffffff" text-anchor="middle">
            {safe_genre.upper()}
        </text>
    </svg>"""

    encoded = base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{encoded}"
