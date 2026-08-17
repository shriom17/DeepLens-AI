"""
URL Processing Service for PaperSense AI

Validates, detects, and processes various URL types:
- PDFs
- Webpages/articles
- Research papers (IEEE, arXiv)
- GitHub profiles and repositories
"""

from typing import Optional, Literal
from enum import Enum
from pydantic import BaseModel
from urllib.parse import urlparse, parse_qs
import re
import requests


class URLType(str, Enum):
    """Supported URL types."""
    PDF = "pdf"
    WEBPAGE = "webpage"
    IEEE_PAPER = "ieee_paper"
    ARXIV_PAPER = "arxiv_paper"
    GITHUB_REPO = "github_repo"
    GITHUB_PROFILE = "github_profile"
    UNKNOWN = "unknown"


class WebpageContent(BaseModel):
    """Extracted webpage content."""
    title: Optional[str] = None
    text: Optional[str] = None
    url: str


class GitHubInfo(BaseModel):
    """GitHub URL information for downstream GitHub service."""
    url_type: Literal["repo", "profile"]
    owner: str
    repo: Optional[str] = None  # Only for repos


class URLProcessingResult(BaseModel):
    """Result of URL processing."""
    success: bool
    url_type: URLType
    url: str
    pdf_bytes: Optional[bytes] = None
    webpage_content: Optional[WebpageContent] = None
    github_info: Optional[GitHubInfo] = None
    error: Optional[str] = None


# HTTP session with safe defaults
def get_safe_session() -> requests.Session:
    """
    Create a requests session with safe defaults.
    
    Returns:
        Configured requests.Session
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "PaperSense-AI/1.0 (+https://github.com/yourusername/papersense-ai)"
    })
    session.timeout = 10  # Default timeout
    return session


def is_valid_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme in ["http", "https"], result.netloc])
    except Exception:
        return False


def detect_url_type(url: str) -> URLType:
    """
    Detect the type of URL.
    
    Args:
        url: URL string
        
    Returns:
        URLType enum value
    """
    url_lower = url.lower()
    
    # PDF URLs
    if url_lower.endswith(".pdf"):
        return URLType.PDF
    
    # GitHub URLs
    if "github.com" in url_lower:
        if re.match(r"https?://github\.com/[^/]+/?$", url):
            return URLType.GITHUB_PROFILE
        else:
            return URLType.GITHUB_REPO
    
    # IEEE URLs
    if "ieeexplore.ieee.org" in url_lower:
        return URLType.IEEE_PAPER
    
    # arXiv URLs
    if "arxiv.org" in url_lower:
        return URLType.ARXIV_PAPER
    
    # Default to webpage
    return URLType.WEBPAGE


def extract_github_info(url: str) -> Optional[GitHubInfo]:
    """
    Extract GitHub repository or profile information.
    
    Args:
        url: GitHub URL
        
    Returns:
        GitHubInfo or None if invalid
    """
    try:
        # Remove .git suffix if present
        url = url.rstrip("/").replace(".git", "")
        
        # Parse URL
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")
        
        if len(path_parts) < 1:
            return None
        
        owner = path_parts[0]
        
        # Profile URL (only owner)
        if len(path_parts) == 1:
            return GitHubInfo(url_type="profile", owner=owner)
        
        # Repository URL (owner/repo)
        if len(path_parts) >= 2:
            repo = path_parts[1]
            return GitHubInfo(url_type="repo", owner=owner, repo=repo)
        
        return None
    
    except Exception:
        return None


def extract_webpage_content(html: str, url: str) -> WebpageContent:
    """
    Extract clean text and title from HTML.
    
    Args:
        html: HTML content
        url: Original URL
        
    Returns:
        WebpageContent with extracted title and text
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return WebpageContent(
            title=None,
            text=None,
            url=url
        )
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract title
        title = None
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
        
        # Remove script and style tags
        for tag in soup(["script", "style"]):
            tag.decompose()
        
        # Extract text
        text = soup.get_text(separator="\n", strip=True)
        
        # Clean excessive whitespace
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)
        
        return WebpageContent(title=title, text=text, url=url)
    
    except Exception:
        return WebpageContent(title=None, text=None, url=url)


def process_url(url: str) -> URLProcessingResult:
    """
    Process a URL and extract relevant content.
    
    Args:
        url: URL string to process
        
    Returns:
        URLProcessingResult with extracted content or error
    """
    # Validate URL
    if not url or not isinstance(url, str):
        return URLProcessingResult(
            success=False,
            url_type=URLType.UNKNOWN,
            url=url or "invalid",
            error="Invalid URL: empty or not a string"
        )
    
    url = url.strip()
    
    if not is_valid_url(url):
        return URLProcessingResult(
            success=False,
            url_type=URLType.UNKNOWN,
            url=url,
            error="Invalid URL format"
        )
    
    # Detect URL type
    url_type = detect_url_type(url)
    
    # Handle GitHub URLs
    if url_type in [URLType.GITHUB_REPO, URLType.GITHUB_PROFILE]:
        github_info = extract_github_info(url)
        if not github_info:
            return URLProcessingResult(
                success=False,
                url_type=url_type,
                url=url,
                error="Invalid GitHub URL format"
            )
        return URLProcessingResult(
            success=True,
            url_type=url_type,
            url=url,
            github_info=github_info
        )
    
    # Fetch content from URL
    session = get_safe_session()
    
    try:
        response = session.get(url, timeout=10, allow_redirects=True, stream=True)
        response.raise_for_status()
        
        content_type = response.headers.get("content-type", "").lower()
        content_length = response.headers.get("content-length")
        
        # Check content length (limit to 50MB for safety)
        if content_length:
            try:
                if int(content_length) > 50 * 1024 * 1024:
                    return URLProcessingResult(
                        success=False,
                        url_type=url_type,
                        url=url,
                        error="Content too large (max 50MB)"
                    )
            except ValueError:
                pass
        
        # Handle PDF
        if "application/pdf" in content_type or url_type == URLType.PDF:
            pdf_bytes = response.content
            return URLProcessingResult(
                success=True,
                url_type=URLType.PDF,
                url=url,
                pdf_bytes=pdf_bytes
            )
        
        # Handle HTML content
        if "text/html" in content_type:
            html = response.text
            content = extract_webpage_content(html, url)
            return URLProcessingResult(
                success=True,
                url_type=url_type,
                url=url,
                webpage_content=content
            )
        
        # Unsupported content type
        return URLProcessingResult(
            success=False,
            url_type=url_type,
            url=url,
            error=f"Unsupported content type: {content_type}"
        )
    
    except requests.exceptions.Timeout:
        return URLProcessingResult(
            success=False,
            url_type=url_type,
            url=url,
            error="Request timeout (URL took too long to respond)"
        )
    
    except requests.exceptions.ConnectionError:
        return URLProcessingResult(
            success=False,
            url_type=url_type,
            url=url,
            error="Connection error (URL is inaccessible)"
        )
    
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            error_msg = "URL requires authentication (login required)"
        elif response.status_code == 403:
            error_msg = "Access forbidden (paywall or permission denied)"
        elif response.status_code == 404:
            error_msg = "URL not found (404)"
        else:
            error_msg = f"HTTP error {response.status_code}"
        
        return URLProcessingResult(
            success=False,
            url_type=url_type,
            url=url,
            error=error_msg
        )
    
    except Exception as e:
        return URLProcessingResult(
            success=False,
            url_type=url_type,
            url=url,
            error=f"Error processing URL: {str(e)}"
        )
    
    finally:
        session.close()
