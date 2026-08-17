"""
GitHub Service for PaperSense AI

Analyzes public GitHub profiles and repositories using the GitHub API.
Collects repository metadata, README, languages, and profile information.
"""

import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import requests


class GitHubRepository(BaseModel):
    """GitHub repository information."""
    name: str
    description: Optional[str] = None
    url: str
    readme: Optional[str] = None
    languages: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    stars: int = 0
    forks: int = 0
    main_files: Optional[List[str]] = None


class GitHubProfile(BaseModel):
    """GitHub user profile information."""
    username: str
    bio: Optional[str] = None
    public_repos_count: int = 0
    public_repositories: Optional[List[Dict[str, Any]]] = None


class GitHubServiceResult(BaseModel):
    """Result of GitHub service operation."""
    success: bool
    repository: Optional[GitHubRepository] = None
    profile: Optional[GitHubProfile] = None
    error: Optional[str] = None


# GitHub API session with authentication
def get_github_session() -> requests.Session:
    """
    Create a requests session for GitHub API with optional authentication.
    
    Returns:
        Configured requests.Session
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "PaperSense-AI/1.0 (+https://github.com/yourusername/papersense-ai)",
        "Accept": "application/vnd.github.v3+json"
    })
    
    # Use GitHub token if available (increases rate limit from 60 to 5000 requests/hour)
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        session.headers.update({
            "Authorization": f"token {github_token}"
        })
    
    session.timeout = 10
    return session


def fetch_repository_languages(owner: str, repo: str, session: requests.Session) -> Optional[List[str]]:
    """
    Fetch programming languages used in repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        session: Requests session
        
    Returns:
        List of languages or None
    """
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/languages"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        languages = response.json()
        return list(languages.keys()) if languages else None
    except Exception:
        return None


def fetch_readme(owner: str, repo: str, session: requests.Session) -> Optional[str]:
    """
    Fetch README content from repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        session: Requests session
        
    Returns:
        README content or None
    """
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        # GitHub API returns README as JSON with content field (base64 encoded)
        readme_data = response.json()
        if "content" in readme_data:
            import base64
            content = base64.b64decode(readme_data["content"]).decode("utf-8")
            return content
        
        return None
    except Exception:
        return None


def fetch_main_files(owner: str, repo: str, session: requests.Session) -> Optional[List[str]]:
    """
    Fetch main files and directories from repository root.
    
    Args:
        owner: Repository owner
        repo: Repository name
        session: Requests session
        
    Returns:
        List of main files/directories or None
    """
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        contents = response.json()
        if isinstance(contents, list):
            names = [item["name"] for item in contents[:20]]  # Limit to first 20 items
            return names
        
        return None
    except Exception:
        return None


def analyze_repository(owner: str, repo: str) -> GitHubServiceResult:
    """
    Analyze a GitHub repository and collect metadata.
    
    Args:
        owner: Repository owner
        repo: Repository name
        
    Returns:
        GitHubServiceResult with repository information or error
    """
    if not owner or not repo:
        return GitHubServiceResult(
            success=False,
            error="Owner and repository name are required"
        )
    
    session = get_github_session()
    
    try:
        # Fetch repository details
        url = f"https://api.github.com/repos/{owner}/{repo}"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        repo_data = response.json()
        
        # Check if repository is private
        if repo_data.get("private", False):
            return GitHubServiceResult(
                success=False,
                error="Private repositories are not supported"
            )
        
        # Fetch additional data in parallel (conceptually)
        readme = fetch_readme(owner, repo, session)
        languages = fetch_repository_languages(owner, repo, session)
        main_files = fetch_main_files(owner, repo, session)
        topics = repo_data.get("topics", [])
        
        repository = GitHubRepository(
            name=repo_data.get("name", repo),
            description=repo_data.get("description"),
            url=repo_data.get("html_url", f"https://github.com/{owner}/{repo}"),
            readme=readme,
            languages=languages,
            topics=topics if topics else None,
            stars=repo_data.get("stargazers_count", 0),
            forks=repo_data.get("forks_count", 0),
            main_files=main_files
        )
        
        return GitHubServiceResult(
            success=True,
            repository=repository
        )
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            error_msg = "Repository not found"
        elif e.response.status_code == 403:
            error_msg = "Access forbidden (rate limit or permission denied)"
        else:
            error_msg = f"HTTP error {e.response.status_code}"
        
        return GitHubServiceResult(
            success=False,
            error=error_msg
        )
    
    except requests.exceptions.Timeout:
        return GitHubServiceResult(
            success=False,
            error="Request timeout (GitHub API took too long)"
        )
    
    except requests.exceptions.ConnectionError:
        return GitHubServiceResult(
            success=False,
            error="Connection error (cannot reach GitHub API)"
        )
    
    except Exception as e:
        return GitHubServiceResult(
            success=False,
            error=f"Error analyzing repository: {str(e)}"
        )
    
    finally:
        session.close()


def analyze_profile(username: str) -> GitHubServiceResult:
    """
    Analyze a GitHub user profile and collect public repositories.
    
    Args:
        username: GitHub username
        
    Returns:
        GitHubServiceResult with profile information or error
    """
    if not username:
        return GitHubServiceResult(
            success=False,
            error="Username is required"
        )
    
    session = get_github_session()
    
    try:
        # Fetch user profile
        user_url = f"https://api.github.com/users/{username}"
        user_response = session.get(user_url, timeout=10)
        user_response.raise_for_status()
        
        user_data = user_response.json()
        
        # Check if user is suspended or deleted
        if user_data.get("message") == "Not Found":
            return GitHubServiceResult(
                success=False,
                error="User not found"
            )
        
        # Fetch public repositories
        repos_url = f"https://api.github.com/users/{username}/repos"
        repos_params = {
            "type": "public",
            "sort": "stars",
            "per_page": 30
        }
        repos_response = session.get(repos_url, params=repos_params, timeout=10)
        repos_response.raise_for_status()
        
        repos_data = repos_response.json()
        
        # Format repositories data
        public_repositories = []
        if isinstance(repos_data, list):
            for repo in repos_data:
                public_repositories.append({
                    "name": repo.get("name"),
                    "description": repo.get("description"),
                    "url": repo.get("html_url"),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0)
                })
        
        profile = GitHubProfile(
            username=user_data.get("login", username),
            bio=user_data.get("bio"),
            public_repos_count=user_data.get("public_repos", 0),
            public_repositories=public_repositories if public_repositories else None
        )
        
        return GitHubServiceResult(
            success=True,
            profile=profile
        )
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            error_msg = "User not found"
        elif e.response.status_code == 403:
            error_msg = "Access forbidden (rate limit or permission denied)"
        else:
            error_msg = f"HTTP error {e.response.status_code}"
        
        return GitHubServiceResult(
            success=False,
            error=error_msg
        )
    
    except requests.exceptions.Timeout:
        return GitHubServiceResult(
            success=False,
            error="Request timeout (GitHub API took too long)"
        )
    
    except requests.exceptions.ConnectionError:
        return GitHubServiceResult(
            success=False,
            error="Connection error (cannot reach GitHub API)"
        )
    
    except Exception as e:
        return GitHubServiceResult(
            success=False,
            error=f"Error analyzing profile: {str(e)}"
        )
    
    finally:
        session.close()
