"""
Paper Analyzer Service for PaperSense AI

Combines PDF extraction, URL processing, and GitHub analysis services
into a unified analysis pipeline with Azure AI integration.
"""

from typing import Optional, Union, List, Dict, Any
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
import os

from backend.services.pdf_extractor import extract_pdf, extract_pdf_from_file, PDFMetadata
from backend.services.url_processor import process_url, URLType, URLProcessingResult
from backend.services.github_service import analyze_repository, analyze_profile
from backend.services.generative_ai import generate_response


class ContentTypeAnalysis(str, Enum):
    """Types of content that can be analyzed."""
    RESEARCH_PAPER_PDF = "research_paper_pdf"
    RESEARCH_PAPER_WEB = "research_paper_web"
    GITHUB_REPOSITORY = "github_repository"
    GITHUB_PROFILE = "github_profile"
    WEB_ARTICLE = "web_article"
    UNKNOWN = "unknown"


class AnalysisMetadata(BaseModel):
    """Metadata about the analyzed content."""
    content_type: ContentTypeAnalysis
    source_url: Optional[str] = None
    source_file: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    date_analyzed: str = None
    page_count: Optional[int] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.date_analyzed:
            self.date_analyzed = datetime.utcnow().isoformat()


class AnalysisResult(BaseModel):
    """Structured analysis result from paper analyzer."""
    success: bool
    metadata: AnalysisMetadata
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    technical_insights: Optional[List[str]] = None
    detailed_analysis: Optional[str] = None
    limitations: Optional[List[str]] = None
    raw_content: Optional[str] = None
    error: Optional[str] = None


def determine_content_type(url_type: URLType, is_research: bool = False) -> ContentTypeAnalysis:
    """
    Determine the content type based on URL type and analysis.
    
    Args:
        url_type: URLType from url_processor
        is_research: Whether content appears to be research paper
        
    Returns:
        ContentTypeAnalysis enum
    """
    if url_type == URLType.PDF:
        return ContentTypeAnalysis.RESEARCH_PAPER_PDF
    elif url_type == URLType.GITHUB_REPO:
        return ContentTypeAnalysis.GITHUB_REPOSITORY
    elif url_type == URLType.GITHUB_PROFILE:
        return ContentTypeAnalysis.GITHUB_PROFILE
    elif url_type in [URLType.IEEE_PAPER, URLType.ARXIV_PAPER]:
        return ContentTypeAnalysis.RESEARCH_PAPER_WEB
    elif url_type == URLType.WEBPAGE:
        return ContentTypeAnalysis.WEB_ARTICLE
    else:
        return ContentTypeAnalysis.UNKNOWN


def extract_key_points(summary: str, content: str) -> List[str]:
    """
    Extract key points from summary and content.
    
    Args:
        summary: Summary text
        content: Full content text
        
    Returns:
        List of key points
    """
    try:
        prompt = f"""Extract 5-7 key points from the following content in bullet format.
Be concise and focus on the most important insights.

Summary: {summary[:500]}

Content: {content[:2000]}

Return only bullet points, one per line, starting with '- '"""
        
        response = generate_response(prompt)
        if response:
            # Parse bullet points
            lines = response.split("\n")
            points = [line.strip("- ").strip() for line in lines if line.strip().startswith("-")]
            return points[:7]
    except Exception:
        pass
    
    return []


def extract_technical_insights(content: str, content_type: ContentTypeAnalysis) -> List[str]:
    """
    Extract technical insights based on content type.
    
    Args:
        content: Full content text
        content_type: Type of content
        
    Returns:
        List of technical insights
    """
    try:
        if content_type == ContentTypeAnalysis.GITHUB_REPOSITORY:
            prompt = f"""Analyze the GitHub repository and provide 5-6 technical insights about:
- Architecture and design patterns
- Technologies and frameworks used
- Code quality indicators
- Community engagement level
- Development activity

Repository content: {content[:2000]}

Return only insights as bullet points starting with '- '"""
        
        elif content_type in [ContentTypeAnalysis.RESEARCH_PAPER_PDF, ContentTypeAnalysis.RESEARCH_PAPER_WEB]:
            prompt = f"""Analyze the research paper and provide 5-6 technical insights about:
- Novel methodologies or approaches
- Experimental findings
- Algorithms or mathematical models used
- Performance improvements or benchmarks
- Limitations of the approach

Paper content: {content[:2000]}

Return only insights as bullet points starting with '- '"""
        
        else:
            prompt = f"""Extract 5-6 technical insights from the following content:

Content: {content[:2000]}

Return only insights as bullet points starting with '- '"""
        
        response = generate_response(prompt)
        if response:
            lines = response.split("\n")
            insights = [line.strip("- ").strip() for line in lines if line.strip().startswith("-")]
            return insights[:6]
    
    except Exception:
        pass
    
    return []


def generate_summary(content: str, content_type: ContentTypeAnalysis) -> Optional[str]:
    """
    Generate a summary based on content type.
    
    Args:
        content: Full content text
        content_type: Type of content
        
    Returns:
        Summary string or None
    """
    try:
        if content_type == ContentTypeAnalysis.GITHUB_REPOSITORY:
            prompt = f"""Write a concise 2-3 sentence summary of this GitHub repository:

{content[:2000]}

Focus on: purpose, main technologies, and key contributions."""
        
        elif content_type in [ContentTypeAnalysis.RESEARCH_PAPER_PDF, ContentTypeAnalysis.RESEARCH_PAPER_WEB]:
            prompt = f"""Write a concise 2-3 sentence summary of this research paper:

{content[:2000]}

Focus on: research question, methodology, and main findings."""
        
        else:
            prompt = f"""Write a concise 2-3 sentence summary of this article:

{content[:2000]}"""
        
        return generate_response(prompt)
    
    except Exception:
        return None


def identify_limitations(content: str, content_type: ContentTypeAnalysis) -> List[str]:
    """
    Identify limitations based on content type.
    
    Args:
        content: Full content text
        content_type: Type of content
        
    Returns:
        List of limitations
    """
    try:
        if content_type == ContentTypeAnalysis.RESEARCH_PAPER_PDF:
            prompt = f"""Identify 3-4 limitations or potential improvements mentioned or implied in this research paper:

{content[:2000]}

Return only limitations as bullet points starting with '- '"""
        
        elif content_type == ContentTypeAnalysis.GITHUB_REPOSITORY:
            prompt = f"""Based on the repository content, identify 3-4 limitations or areas for improvement:

{content[:2000]}

Return only limitations as bullet points starting with '- '"""
        
        else:
            return []
        
        response = generate_response(prompt)
        if response:
            lines = response.split("\n")
            limitations = [line.strip("- ").strip() for line in lines if line.strip().startswith("-")]
            return limitations[:4]
    
    except Exception:
        pass
    
    return []


def analyze_pdf(pdf_bytes: bytes, filename: Optional[str] = None) -> AnalysisResult:
    """
    Analyze a PDF file.
    
    Args:
        pdf_bytes: PDF file bytes
        filename: Optional filename
        
    Returns:
        AnalysisResult
    """
    # Extract PDF metadata
    extraction = extract_pdf(pdf_bytes, filename)
    
    if not extraction.success:
        return AnalysisResult(
            success=False,
            metadata=AnalysisMetadata(content_type=ContentTypeAnalysis.UNKNOWN),
            error=extraction.error or "Failed to process PDF"
        )
    
    metadata = AnalysisMetadata(
        content_type=ContentTypeAnalysis.RESEARCH_PAPER_PDF,
        source_file=filename,
        title=extraction.metadata.title,
        author=extraction.metadata.author,
        page_count=extraction.metadata.page_count
    )
    
    # For now, return metadata and placeholder for Azure Content Understanding integration
    # Azure Content Understanding would be called here for advanced document analysis
    try:
        summary = "PDF analysis ready for Azure Content Understanding processing."
        
        return AnalysisResult(
            success=True,
            metadata=metadata,
            summary=summary,
            raw_content=f"PDF: {extraction.metadata.page_count} pages, Title: {extraction.metadata.title}"
        )
    
    except Exception as e:
        return AnalysisResult(
            success=False,
            metadata=metadata,
            error=f"Error analyzing PDF: {str(e)}"
        )


def analyze_url(url: str) -> AnalysisResult:
    """
    Analyze content from a URL.
    
    Args:
        url: URL to analyze
        
    Returns:
        AnalysisResult
    """
    # Process URL
    url_result = process_url(url)
    
    if not url_result.success:
        return AnalysisResult(
            success=False,
            metadata=AnalysisMetadata(content_type=ContentTypeAnalysis.UNKNOWN, source_url=url),
            error=url_result.error or "Failed to process URL"
        )
    
    # Handle GitHub URLs
    if url_result.url_type == URLType.GITHUB_REPO and url_result.github_info:
        gh_result = analyze_repository(
            url_result.github_info.owner,
            url_result.github_info.repo
        )
        
        if gh_result.success and gh_result.repository:
            repo = gh_result.repository
            content = f"Repository: {repo.name}\nDescription: {repo.description}\nLanguages: {repo.languages}\nStars: {repo.stars}\nREADME: {repo.readme[:1000] if repo.readme else 'Not available'}"
            
            metadata = AnalysisMetadata(
                content_type=ContentTypeAnalysis.GITHUB_REPOSITORY,
                source_url=url,
                title=repo.name
            )
            
            summary = generate_summary(content, ContentTypeAnalysis.GITHUB_REPOSITORY)
            key_points = extract_key_points(summary or "", content)
            technical_insights = extract_technical_insights(content, ContentTypeAnalysis.GITHUB_REPOSITORY)
            
            return AnalysisResult(
                success=True,
                metadata=metadata,
                summary=summary,
                key_points=key_points,
                technical_insights=technical_insights,
                raw_content=content
            )
        else:
            return AnalysisResult(
                success=False,
                metadata=AnalysisMetadata(content_type=ContentTypeAnalysis.GITHUB_REPOSITORY, source_url=url),
                error=gh_result.error or "Failed to analyze GitHub repository"
            )
    
    # Handle GitHub profile URLs
    if url_result.url_type == URLType.GITHUB_PROFILE and url_result.github_info:
        gh_result = analyze_profile(url_result.github_info.owner)
        
        if gh_result.success and gh_result.profile:
            profile = gh_result.profile
            repos_str = "\n".join([f"- {r['name']}: {r['description']}" for r in (profile.public_repositories or [])[:5]])
            content = f"Profile: {profile.username}\nBio: {profile.bio}\nPublic Repos: {profile.public_repos_count}\nTop repos:\n{repos_str}"
            
            metadata = AnalysisMetadata(
                content_type=ContentTypeAnalysis.GITHUB_PROFILE,
                source_url=url,
                title=profile.username
            )
            
            summary = generate_summary(content, ContentTypeAnalysis.GITHUB_PROFILE)
            
            return AnalysisResult(
                success=True,
                metadata=metadata,
                summary=summary,
                raw_content=content
            )
        else:
            return AnalysisResult(
                success=False,
                metadata=AnalysisMetadata(content_type=ContentTypeAnalysis.GITHUB_PROFILE, source_url=url),
                error=gh_result.error or "Failed to analyze GitHub profile"
            )
    
    # Handle PDF URLs
    if url_result.url_type == URLType.PDF and url_result.pdf_bytes:
        return analyze_pdf(url_result.pdf_bytes, filename=url)
    
    # Handle web content (articles, webpages, research papers)
    if url_result.webpage_content:
        content = url_result.webpage_content.text or ""
        title = url_result.webpage_content.title
        
        content_type = determine_content_type(url_result.url_type)
        
        metadata = AnalysisMetadata(
            content_type=content_type,
            source_url=url,
            title=title
        )
        
        summary = generate_summary(content, content_type)
        key_points = extract_key_points(summary or "", content)
        technical_insights = extract_technical_insights(content, content_type)
        limitations = identify_limitations(content, content_type)
        
        return AnalysisResult(
            success=True,
            metadata=metadata,
            summary=summary,
            key_points=key_points,
            technical_insights=technical_insights,
            limitations=limitations if limitations else None,
            raw_content=content[:2000]  # Store first 2000 chars
        )
    
    return AnalysisResult(
        success=False,
        metadata=AnalysisMetadata(content_type=ContentTypeAnalysis.UNKNOWN, source_url=url),
        error="Unable to extract content from URL"
    )


def analyze(source: Union[bytes, str], filename: Optional[str] = None) -> AnalysisResult:
    """
    Main entry point for paper analysis.
    
    Accepts either PDF bytes or a URL string and returns comprehensive analysis.
    
    Args:
        source: Either PDF bytes or a URL string
        filename: Optional filename for PDF uploads
        
    Returns:
        AnalysisResult with comprehensive analysis
    """
    if isinstance(source, bytes):
        return analyze_pdf(source, filename)
    elif isinstance(source, str):
        return analyze_url(source)
    else:
        return AnalysisResult(
            success=False,
            metadata=AnalysisMetadata(content_type=ContentTypeAnalysis.UNKNOWN),
            error="Invalid source: expected bytes or string URL"
        )
