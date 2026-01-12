from urllib.parse import urlparse

def score_url(url: str) -> dict:
    """
    Score a URL based on credibility indicators.
    Returns a dictionary with url, score (0-100), and is_trusted flag.
    """
    score = 50  # Start neutral
    domain = urlparse(url).netloc.lower()
    path = urlparse(url).path.lower()
    
    # 1. Trusted Domains (Boost Score)
    trusted_endings = ['.gov', '.edu', '.org', '.mil']
    if any(domain.endswith(t) for t in trusted_endings):
        score += 30
        
    # 2. Trusted Platforms (Medium Boost)
    # You can add sites like 'reuters.com', 'nature.com' here
    authoritative = ['wikipedia.org', 'arxiv.org', 'nih.gov', 'reuters.com', 
                     'nature.com', 'science.org', 'ieee.org', 'acm.org',
                     'scholar.google.com', 'pubmed.ncbi.nlm.nih.gov']
    if any(site in domain for site in authoritative):
        score += 20

    # 3. Penalties (Reduce Score)
    suspicious = ['blogspot', 'wordpress', 'wixsite', 'tumblr.com']
    if any(s in domain for s in suspicious):
        score -= 20
        
    # 4. HTTPS Check
    if url.startswith('https://'):
        score += 10
    else:
        score -= 10  # Penalty for HTTP
        
    # 5. Path-based indicators
    if '/blog/' in path or '/post/' in path:
        score -= 5  # Likely a blog post
    if '/research/' in path or '/paper/' in path or '/publication/' in path:
        score += 15  # Likely academic content
        
    # Clamp score between 0 and 100
    final_score = max(0, min(100, score))
    
    return {
        "url": url,
        "score": final_score,
        "is_trusted": final_score > 65
    }
