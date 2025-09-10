#!/usr/bin/env python3
"""
Enhanced Research Mode for Omnix AI
Features:
- Multi-source research and analysis
- Advanced fact-checking and validation
- Research synthesis and insight generation
- Citation management and source tracking
- Research methodology optimization
"""

import asyncio
import logging
import json
import time
import aiohttp
import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from urllib.parse import urlparse, quote
import hashlib
from bs4 import BeautifulSoup
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


@dataclass
class ResearchSource:
    """Represents a research source"""
    url: str
    title: str
    content: str
    credibility_score: float
    source_type: str  # academic, news, blog, government, etc.
    publish_date: Optional[str] = None
    author: Optional[str] = None
    domain: Optional[str] = None
    citations: int = 0
    
    def __post_init__(self):
        if self.domain is None:
            self.domain = urlparse(self.url).netloc


@dataclass
class ResearchFindings:
    """Represents research findings from multiple sources"""
    query: str
    sources: List[ResearchSource]
    synthesis: str
    confidence_score: float
    key_insights: List[str]
    contradictions: List[str]
    gaps: List[str]
    recommendations: List[str]
    timestamp: float


class AdvancedWebSearcher:
    """Advanced web search with multiple search engines and sources"""
    
    def __init__(self, brave_api_key: str = None, serpapi_key: str = None):
        self.brave_api_key = brave_api_key
        self.serpapi_key = serpapi_key
        self.logger = logging.getLogger(__name__)
        
        # Academic and specialized search endpoints
        self.academic_apis = {
            'crossref': 'https://api.crossref.org/works',
            'arxiv': 'http://export.arxiv.org/api/query',
            'pubmed': 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
        }
        
        self.logger.info("🔍 Advanced Web Searcher initialized")
    
    def _is_academic_query(self, query: str) -> bool:
        """Determine if a query should include academic sources"""
        query_lower = query.lower()
        
        # Natural phenomena that should use general web search (not academic)
        natural_phenomena = [
            'northern lights', 'aurora', 'southern lights', 'rainbow', 'lightning',
            'tornado', 'hurricane', 'earthquake', 'volcano', 'eclipse', 'meteor',
            'comet', 'sunset', 'sunrise', 'weather', 'storm', 'snow', 'rain'
        ]
        
        # Consumer/everyday indicators (avoid academic search)
        consumer_indicators = [
            'buy', 'purchase', 'price', 'cost', 'where to find', 'how to make',
            'recipe', 'diy', 'tutorial', 'guide', 'tips', 'tricks', 'review',
            'best', 'vs', 'comparison', 'brand', 'product', 'store', 'restaurant',
            'food', 'cooking', 'travel', 'vacation', 'entertainment', 'movie',
            'music', 'game', 'sports', 'news', 'celebrity', 'fashion', 'when to see',
            'best time', 'viewing', 'watch', 'observe'
        ]
        
        # Technical/research topics that benefit from academic sources
        technical_topics = [
            'renewable energy', 'climate change', 'artificial intelligence', 'machine learning',
            'quantum computing', 'biotechnology', 'nanotechnology', 'blockchain',
            'cybersecurity', 'data science', 'sustainability', 'environmental impact',
            'carbon footprint', 'greenhouse gas', 'biodiversity', 'ecosystem',
            'pharmaceutical', 'medical research', 'clinical', 'genomics', 'biomedical',
            'engineering', 'materials science', 'semiconductor', 'nuclear energy',
            'solar energy', 'wind energy', 'battery technology', 'electric vehicles'
        ]
        
        # Academic indicators (technical research terms)
        academic_indicators = [
            'peer review', 'journal article', 'research paper', 'methodology',
            'experiment design', 'clinical trial', 'statistical analysis', 'meta-analysis',
            'systematic review', 'correlation coefficient', 'regression analysis',
            'hypothesis testing', 'comprehensive analysis', 'trends', 'adoption',
            'biochemical pathway', 'molecular mechanism', 'genetic expression'
        ]
        
        # Check for natural phenomena first (these use general web search)
        if any(phenomenon in query_lower for phenomenon in natural_phenomena):
            return False
        
        # Check for consumer indicators (these override academic)
        if any(indicator in query_lower for indicator in consumer_indicators):
            return False
        
        # Check for technical topics that benefit from academic sources
        if any(topic in query_lower for topic in technical_topics):
            return True
        
        # Check for academic indicators (research terms)
        if any(indicator in query_lower for indicator in academic_indicators):
            return True
        
        # Default: non-academic for general questions
        return False
    
    def _format_arxiv_query(self, query: str) -> str:
        """Format query for arXiv API to handle compound terms better"""
        # If query contains multiple words, treat as phrase for better results
        words = query.strip().split()
        if len(words) > 1:
            # Use quotes for compound terms to search as phrase
            return f'all:"{query}"'
        else:
            return f'all:{query}'
    
    async def multi_source_search(self, query: str, max_results: int = 75) -> List[ResearchSource]:
        """Perform search across multiple sources and engines"""
        
        all_sources = []
        
        # Search tasks to run in parallel
        search_tasks = []
        
        # Determine if query is academic/scientific in nature
        is_academic = self._is_academic_query(query)
        
        # Allocate search sources based on query type
        if is_academic:
            # Academic queries: balanced allocation
            web_allocation = max_results // 4
            news_allocation = max_results // 4
            specialized_allocation = max_results // 4
            academic_allocation = max_results // 4
        else:
            # Non-academic queries: prioritize web and news
            web_allocation = max_results // 2
            news_allocation = max_results // 3
            specialized_allocation = max_results // 6
            academic_allocation = 0
        
        # General web search
        if self.brave_api_key:
            search_tasks.append(self._brave_search(query, web_allocation))
        
        # Academic search (only for clearly academic/scientific queries)
        if is_academic and academic_allocation > 0:
            search_tasks.append(self._academic_search(query, academic_allocation))
        
        # News search
        search_tasks.append(self._news_search(query, news_allocation))
        
        # Specialized search (government, organizations)
        search_tasks.append(self._specialized_search(query, specialized_allocation))
        
        # Execute all searches in parallel
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Combine results
        for result in search_results:
            if isinstance(result, list):
                all_sources.extend(result)
            elif isinstance(result, Exception):
                self.logger.warning(f"Search task failed: {result}")
        
        # Deduplicate and rank sources
        unique_sources = self._deduplicate_sources(all_sources)
        ranked_sources = self._rank_sources(unique_sources, query)
        
        return ranked_sources[:max_results]
    
    async def _brave_search(self, query: str, max_results: int) -> List[ResearchSource]:
        """Search using Brave Search API"""
        
        if not self.brave_api_key:
            return []
        
        try:
            headers = {"X-Subscription-Token": self.brave_api_key}
            # Brave API has a limit of 20 per request, so we cap it
            count = min(max_results, 20)
            params = {"q": query, "count": count}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        sources = []
                        
                        for result in data.get("web", {}).get("results", []):
                            source = ResearchSource(
                                url=result.get("url", ""),
                                title=result.get("title", ""),
                                content=result.get("description", ""),
                                credibility_score=self._assess_credibility(result.get("url", "")),
                                source_type="web",
                                domain=urlparse(result.get("url", "")).netloc
                            )
                            sources.append(source)
                        
                        return sources
            
        except Exception as e:
            self.logger.error(f"Brave search failed: {e}")
        
        return []
    
    async def _academic_search(self, query: str, max_results: int) -> List[ResearchSource]:
        """Search academic sources"""
        
        sources = []
        
        # Search arXiv
        try:
            arxiv_sources = await self._search_arxiv(query, max_results // 2)
            sources.extend(arxiv_sources)
        except Exception as e:
            self.logger.warning(f"arXiv search failed: {e}")
        
        # Search CrossRef for academic papers
        try:
            crossref_sources = await self._search_crossref(query, max_results // 2)
            sources.extend(crossref_sources)
        except Exception as e:
            self.logger.warning(f"CrossRef search failed: {e}")
        
        return sources
    
    async def _search_arxiv(self, query: str, max_results: int) -> List[ResearchSource]:
        """Search arXiv for academic papers"""
        
        try:
            # Format query for better compound term handling
            formatted_query = self._format_arxiv_query(query)
            params = {
                'search_query': formatted_query,
                'start': 0,
                'max_results': max_results,
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.academic_apis['arxiv'], params=params) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Parse arXiv XML response
                        sources = self._parse_arxiv_response(content)
                        return sources
            
        except Exception as e:
            self.logger.error(f"arXiv search error: {e}")
        
        return []
    
    def _parse_arxiv_response(self, xml_content: str) -> List[ResearchSource]:
        """Parse arXiv XML response"""
        sources = []
        
        try:
            from xml.etree import ElementTree as ET
            root = ET.fromstring(xml_content)
            
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
                id_elem = entry.find('{http://www.w3.org/2005/Atom}id')
                published_elem = entry.find('{http://www.w3.org/2005/Atom}published')
                
                if title_elem is not None and id_elem is not None:
                    source = ResearchSource(
                        url=id_elem.text,
                        title=title_elem.text.strip(),
                        content=summary_elem.text.strip() if summary_elem is not None else "",
                        credibility_score=0.9,  # arXiv papers are generally credible
                        source_type="academic",
                        publish_date=published_elem.text if published_elem is not None else None,
                        domain="arxiv.org"
                    )
                    sources.append(source)
            
        except Exception as e:
            self.logger.error(f"Error parsing arXiv response: {e}")
        
        return sources
    
    async def _search_crossref(self, query: str, max_results: int) -> List[ResearchSource]:
        """Search CrossRef for academic papers"""
        
        try:
            # Format query for better compound term handling in CrossRef
            formatted_query = f'"{query}"' if len(query.split()) > 1 else query
            params = {
                'query': formatted_query,
                'rows': max_results,
                'sort': 'relevance',
                'order': 'desc'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.academic_apis['crossref'], params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        sources = []
                        
                        for item in data.get('message', {}).get('items', []):
                            title = ' '.join(item.get('title', ['']))
                            abstract = ' '.join(item.get('abstract', ['']))
                            url = item.get('URL', '')
                            
                            if title and url:
                                source = ResearchSource(
                                    url=url,
                                    title=title,
                                    content=abstract,
                                    credibility_score=0.95,  # Academic papers are highly credible
                                    source_type="academic",
                                    publish_date=self._extract_date(item),
                                    author=self._extract_authors(item),
                                    citations=item.get('is-referenced-by-count', 0)
                                )
                                sources.append(source)
                        
                        return sources
            
        except Exception as e:
            self.logger.error(f"CrossRef search error: {e}")
        
        return []
    
    def _extract_date(self, item: Dict) -> Optional[str]:
        """Extract publication date from CrossRef item"""
        date_parts = item.get('published-print', {}).get('date-parts')
        if not date_parts or not date_parts[0]:
            date_parts = item.get('published-online', {}).get('date-parts')
        
        if date_parts and date_parts[0]:
            return f"{date_parts[0][0]}-{date_parts[0][1]:02d}-{date_parts[0][2]:02d}" if len(date_parts[0]) >= 3 else str(date_parts[0][0])
        
        return None
    
    def _extract_authors(self, item: Dict) -> Optional[str]:
        """Extract authors from CrossRef item"""
        authors = item.get('author', [])
        if authors:
            author_names = []
            for author in authors[:3]:  # Limit to first 3 authors
                given = author.get('given', '')
                family = author.get('family', '')
                if family:
                    author_names.append(f"{given} {family}".strip())
            
            if author_names:
                result = ', '.join(author_names)
                if len(authors) > 3:
                    result += ' et al.'
                return result
        
        return None
    
    async def _news_search(self, query: str, max_results: int) -> List[ResearchSource]:
        """Search news sources"""
        
        # This would integrate with news APIs like NewsAPI
        # For now, return empty list as placeholder
        return []
    
    async def _specialized_search(self, query: str, max_results: int) -> List[ResearchSource]:
        """Search specialized sources (government, organizations)"""
        
        # This would search government databases, organization reports, etc.
        # For now, return empty list as placeholder
        return []
    
    def _assess_credibility(self, url: str) -> float:
        """Assess the credibility of a source based on its URL"""
        
        domain = urlparse(url).netloc.lower()
        
        # High credibility domains
        high_credibility = [
            'arxiv.org', 'pubmed.ncbi.nlm.nih.gov', 'scholar.google.com',
            'ieee.org', 'acm.org', 'nature.com', 'science.org',
            'gov', 'edu', 'who.int', 'cdc.gov', 'nih.gov'
        ]
        
        # Medium credibility domains
        medium_credibility = [
            'wikipedia.org', 'reuters.com', 'bbc.com', 'npr.org',
            'economist.com', 'wsj.com', 'nytimes.com'
        ]
        
        # Check for high credibility
        for hc_domain in high_credibility:
            if hc_domain in domain:
                return 0.9
        
        # Check for medium credibility
        for mc_domain in medium_credibility:
            if mc_domain in domain:
                return 0.7
        
        # Check for academic indicators
        if any(indicator in domain for indicator in ['.edu', '.ac.', 'university', 'college']):
            return 0.85
        
        # Check for government indicators
        if any(indicator in domain for indicator in ['.gov', '.mil', 'government']):
            return 0.8
        
        # Default credibility
        return 0.5
    
    def _deduplicate_sources(self, sources: List[ResearchSource]) -> List[ResearchSource]:
        """Remove duplicate sources"""
        
        seen_urls = set()
        unique_sources = []
        
        for source in sources:
            if source.url not in seen_urls:
                seen_urls.add(source.url)
                unique_sources.append(source)
        
        return unique_sources
    
    def _rank_sources(self, sources: List[ResearchSource], query: str) -> List[ResearchSource]:
        """Rank sources by relevance and credibility"""
        
        query_terms = query.lower().split()
        
        def calculate_score(source: ResearchSource) -> float:
            # Base credibility score
            score = source.credibility_score
            
            # Relevance based on exact phrase matching (higher priority)
            title_lower = source.title.lower()
            content_lower = source.content.lower()
            query_lower = query.lower()
            
            # Boost for exact phrase matches
            if query_lower in title_lower:
                score += 1.0  # High boost for exact title match
            elif query_lower in content_lower:
                score += 0.5  # Medium boost for exact content match
            
            # Individual term matches (lower priority)
            title_matches = sum(1 for term in query_terms if term in title_lower and len(term) > 3)
            content_matches = sum(1 for term in query_terms if term in content_lower and len(term) > 3)
            
            relevance_score = (title_matches * 2 + content_matches) / max(len(query_terms) * 3, 1)
            score += relevance_score * 0.3
            
            # Penalize sources with very short or generic content
            if len(source.content) < 50:
                score -= 0.2
            
            # Boost for citations (if available)
            if source.citations > 0:
                score += min(source.citations / 100, 0.2)  # Cap at 0.2 boost
            
            # Boost for academic sources on technical topics
            if source.source_type == "academic":
                score += 0.15
            
            return score
        
        # Sort by calculated score
        sources.sort(key=calculate_score, reverse=True)
        return sources


class ContentExtractor:
    """Extract and process content from web sources"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def extract_full_content(self, sources: List[ResearchSource]) -> List[ResearchSource]:
        """Extract full content from source URLs"""
        
        extraction_tasks = []
        for source in sources:
            extraction_tasks.append(self._extract_source_content(source))
        
        extracted_sources = await asyncio.gather(*extraction_tasks, return_exceptions=True)
        
        valid_sources = []
        for result in extracted_sources:
            if isinstance(result, ResearchSource):
                valid_sources.append(result)
            elif isinstance(result, Exception):
                self.logger.warning(f"Content extraction failed: {result}")
        
        return valid_sources
    
    async def _extract_source_content(self, source: ResearchSource) -> ResearchSource:
        """Extract content from a single source"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    source.url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; ResearchBot/1.0)'}
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Parse HTML content
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Extract main content
                        text_content = soup.get_text()
                        
                        # Clean up text
                        cleaned_text = self._clean_text(text_content)
                        
                        # Update source with full content
                        source.content = cleaned_text[:5000]  # Limit to 5000 characters
                        
                        return source
            
        except Exception as e:
            self.logger.warning(f"Failed to extract content from {source.url}: {e}")
        
        return source
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        
        return text.strip()


class SimpleGeminiResearcher:
    """Simple Gemini 2.5 Pro researcher with thinking mode - like Perplexity Pro"""
    
    def __init__(self, google_api_key: str):
        self.google_api_key = google_api_key
        self.logger = logging.getLogger(__name__)
        
        # Configure Gemini API
        genai.configure(api_key=google_api_key)
        
        # Initialize Gemini 2.5 Pro with thinking capabilities
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-pro',
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
            generation_config={
                'temperature': 0.3,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 8192,
            }
        )
        
        self.logger.info("🚀 Simple Gemini Researcher initialized (Perplexity Pro style)")
    
    async def research_with_thinking(self, query: str, sources_text: str) -> str:
        """Research synthesis with thinking mode enabled"""
        
        thinking_prompt = f"""
<thinking>
I need to synthesize comprehensive research findings for the query: "{query}"

Let me analyze the sources systematically:
1. Extract key facts and claims from each source
2. Identify patterns and consensus points
3. Note any contradictions or debates
4. Evaluate source credibility and reliability
5. Synthesize into a coherent, well-structured response

This should be like Perplexity Pro - comprehensive but clear and accessible.
</thinking>

You are a research AI that provides comprehensive, well-sourced analysis like Perplexity Pro.

Query: {query}

Sources analyzed:
{sources_text}

Provide a comprehensive research summary that includes:

1. **Executive Summary** - Key findings in 2-3 sentences
2. **Detailed Analysis** - Main insights with source references
3. **Key Points** - 3-5 bullet points of critical information
4. **Confidence Level** - High/Medium/Low based on source quality

Be thorough but accessible. Reference sources naturally in your analysis.
        """
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                thinking_prompt
            )
            
            return response.text if response.text else "Research analysis completed."
            
        except Exception as e:
            self.logger.error(f"Research synthesis failed: {e}")
            return f"Research completed for: {query}. Please try again if more detail is needed."


class ResearchSynthesizer:
    """Synthesize research findings from multiple sources"""
    
    def __init__(self, google_api_key: str):
        self.researcher = SimpleGeminiResearcher(google_api_key)
        self.logger = logging.getLogger(__name__)
    
    async def synthesize_research(self, query: str, sources: List[ResearchSource]) -> ResearchFindings:
        """Synthesize research findings from multiple sources"""
        
        self.logger.info(f"🔬 Synthesizing research for: {query}")
        
        # Prepare source information for analysis
        source_summaries = []
        for i, source in enumerate(sources):
            summary = f"""
            Source {i+1}:
            Title: {source.title}
            URL: {source.url}
            Type: {source.source_type}
            Credibility: {source.credibility_score:.2f}
            Content: {source.content[:500]}...
            """
            source_summaries.append(summary)
        
        # Create synthesis prompt
        synthesis_prompt = f"""
        Conduct a comprehensive research synthesis for the query: "{query}"
        
        You have access to {len(sources)} research sources. Analyze these sources and provide:
        
        1. COMPREHENSIVE SYNTHESIS
           - Integrate findings from all sources
           - Identify common themes and patterns
           - Highlight key discoveries and insights
        
        2. CREDIBILITY ASSESSMENT
           - Evaluate the overall reliability of findings
           - Note any source bias or limitations
           - Assess the strength of evidence
        
        3. CONTRADICTIONS AND CONFLICTS
           - Identify any conflicting information between sources
           - Analyze potential reasons for contradictions
           - Assess which sources are more reliable for conflicting claims
        
        4. KNOWLEDGE GAPS
           - Identify areas where information is incomplete
           - Note questions that remain unanswered
           - Suggest areas for further research
        
        5. KEY INSIGHTS AND IMPLICATIONS
           - Extract the most important insights
           - Discuss practical implications
           - Provide actionable recommendations
        
        6. CONFIDENCE ASSESSMENT
           - Rate your confidence in the findings (0.0 to 1.0)
           - Explain factors affecting confidence
        
        Sources to analyze:
        {chr(10).join(source_summaries)}
        
        Provide a thorough, well-structured analysis that demonstrates critical thinking and research methodology.
        """
        
        # Get synthesis from Gemini with thinking
        synthesis_text = await self.researcher.research_with_thinking(
            query, 
            "\n\n".join(source_summaries)
        )
        
        # Extract confidence level from response
        confidence_score = self._extract_confidence(synthesis_text)
        
        findings = ResearchFindings(
            query=query,
            sources=sources,
            synthesis=synthesis_text,
            confidence_score=confidence_score,
            key_insights=self._extract_insights(synthesis_text),
            contradictions=self._extract_contradictions(synthesis_text),
            gaps=self._extract_gaps(synthesis_text),
            recommendations=self._extract_recommendations(synthesis_text),
            timestamp=time.time()
        )
        
        self.logger.info(f"✅ Research synthesis completed with {len(findings.key_insights)} insights")
        
        return findings
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence level from response text"""
        text_lower = text.lower()
        if 'high confidence' in text_lower or 'confidence level: high' in text_lower:
            return 0.9
        elif 'medium confidence' in text_lower or 'confidence level: medium' in text_lower:
            return 0.7
        elif 'low confidence' in text_lower or 'confidence level: low' in text_lower:
            return 0.5
        else:
            # Default based on source count and quality
            return 0.8
    
    def _extract_insights(self, text: str) -> List[str]:
        """Extract key insights from synthesis text"""
        insights = []
        lines = text.split('\n')
        
        in_insights_section = False
        for line in lines:
            if 'insight' in line.lower() or 'key finding' in line.lower():
                in_insights_section = True
            elif in_insights_section and line.strip():
                if line.strip().startswith(('-', '•', '*', '1.', '2.', '3.')):
                    insights.append(line.strip())
                elif not any(marker in line.lower() for marker in ['contradiction', 'gap', 'recommendation']):
                    insights.append(line.strip())
                else:
                    break
        
        return insights[:5]  # Return top 5 insights
    
    def _extract_contradictions(self, text: str) -> List[str]:
        """Extract contradictions from synthesis text"""
        contradictions = []
        lines = text.split('\n')
        
        in_contradictions_section = False
        for line in lines:
            if 'contradiction' in line.lower() or 'conflict' in line.lower():
                in_contradictions_section = True
            elif in_contradictions_section and line.strip():
                if line.strip().startswith(('-', '•', '*', '1.', '2.', '3.')):
                    contradictions.append(line.strip())
                elif not any(marker in line.lower() for marker in ['gap', 'recommendation', 'insight']):
                    contradictions.append(line.strip())
                else:
                    break
        
        return contradictions[:3]  # Return top 3 contradictions
    
    def _extract_gaps(self, text: str) -> List[str]:
        """Extract knowledge gaps from synthesis text"""
        gaps = []
        lines = text.split('\n')
        
        in_gaps_section = False
        for line in lines:
            if 'gap' in line.lower() or 'incomplete' in line.lower() or 'unanswered' in line.lower():
                in_gaps_section = True
            elif in_gaps_section and line.strip():
                if line.strip().startswith(('-', '•', '*', '1.', '2.', '3.')):
                    gaps.append(line.strip())
                elif not any(marker in line.lower() for marker in ['recommendation', 'insight', 'contradiction']):
                    gaps.append(line.strip())
                else:
                    break
        
        return gaps[:3]  # Return top 3 gaps
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from synthesis text"""
        recommendations = []
        lines = text.split('\n')
        
        in_recommendations_section = False
        for line in lines:
            if 'recommendation' in line.lower() or 'suggest' in line.lower():
                in_recommendations_section = True
            elif in_recommendations_section and line.strip():
                if line.strip().startswith(('-', '•', '*', '1.', '2.', '3.')):
                    recommendations.append(line.strip())
                elif not any(marker in line.lower() for marker in ['gap', 'insight', 'contradiction']):
                    recommendations.append(line.strip())
                else:
                    break
        
        return recommendations[:5]  # Return top 5 recommendations


class EnhancedResearchManager:
    """Main manager for enhanced research capabilities - Perplexity Pro style"""
    
    def __init__(self, google_api_key: str, brave_api_key: str = None, serpapi_key: str = None):
        self.google_api_key = google_api_key
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.searcher = AdvancedWebSearcher(brave_api_key, serpapi_key)
        self.extractor = ContentExtractor()
        self.synthesizer = ResearchSynthesizer(google_api_key)
        
        # Research cache
        self.research_cache = {}
        
        self.logger.info("🔬 Enhanced Research Manager initialized (Perplexity Pro style)")
    
    async def _initialize_research_thinking(self, query: str) -> Dict[str, Any]:
        """Initialize sequential thinking process for research"""
        
        thinking_prompt = f"""
        Initialize sequential thinking for comprehensive research on: "{query}"
        
        RESEARCH THINKING FRAMEWORK:
        1. QUERY ANALYSIS: Break down the research question
        2. SCOPE DEFINITION: Determine research boundaries and depth needed
        3. SOURCE STRATEGY: Plan optimal source types and search strategies
        4. VALIDATION APPROACH: Define fact-checking and credibility assessment
        5. SYNTHESIS PLAN: Outline how to combine findings coherently
        
        Provide initial thinking for each step.
        """
        
        try:
            # Simple Gemini 2.5 Pro thinking approach
            researcher = SimpleGeminiResearcher(self.google_api_key)
            response = await researcher.research_with_thinking(
                f"Research planning for: {query}", 
                thinking_prompt
            )
            
            return {
                "initial_thinking": response,
                "query": query,
                "timestamp": time.time()
            }
        except Exception as e:
            self.logger.warning(f"Failed to initialize research thinking: {e}")
            return {"initial_thinking": "Basic research approach", "query": query}
    
    async def _comprehensive_multi_source_search(
        self, 
        query: str, 
        max_sources: int
    ) -> List[ResearchSource]:
        """Conduct comprehensive search across multiple engines and source types"""
        
        all_sources = []
        
        # Multiple search rounds with different query variations
        query_variations = self._generate_query_variations(query)
        
        search_tasks = []
        
        for variation in query_variations:
            # General web search (multiple rounds)
            if self.searcher.brave_api_key:
                search_tasks.append(self.searcher._brave_search(variation, max_sources // len(query_variations)))
            
            # Academic search
            search_tasks.append(self.searcher._academic_search(variation, max_sources // len(query_variations)))
            
            # News search
            search_tasks.append(self.searcher._news_search(variation, max_sources // len(query_variations)))
            
            # Specialized search
            search_tasks.append(self.searcher._specialized_search(variation, max_sources // len(query_variations)))
        
        # Execute all searches in parallel
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Combine and deduplicate results
        seen_urls = set()
        for result in search_results:
            if isinstance(result, list):
                for source in result:
                    if source.url not in seen_urls:
                        all_sources.append(source)
                        seen_urls.add(source.url)
        
        # Use ALL available sources found (no minimum requirement)
        self.logger.info(f"🎯 Collected {len(all_sources)} total sources from all searches")
        
        return all_sources[:max_sources]
    
    def _generate_query_variations(self, query: str) -> List[str]:
        """Generate smart variations of the query for comprehensive search"""
        
        variations = [query]
        
        # Add quoted version for exact phrase search (keeps compound terms together)
        variations.append(f'"{query}"')
        
        # Instead of breaking into individual words, create meaningful phrase combinations
        words = query.split()
        if len(words) > 2:
            # Create meaningful 2-3 word combinations instead of single words
            for i in range(len(words) - 1):
                phrase = " ".join(words[i:i+2])  # 2-word phrases
                if len(phrase.split()) == 2 and len(phrase) > 8:  # Only meaningful phrases
                    variations.append(phrase)
                
                # Add 3-word phrases for longer queries
                if i < len(words) - 2:
                    phrase3 = " ".join(words[i:i+3])
                    if len(phrase3.split()) == 3:
                        variations.append(phrase3)
        
        # Add context-specific research terms
        research_terms = ['latest', '2024', 'current', 'recent']
        for term in research_terms[:2]:  # Limit to 2 to avoid overload
            variations.append(f"{query} {term}")
        
        # Limit variations to prevent search overload
        return variations[:5]
    
    async def _emergency_search_boost(self, query: str, needed_count: int) -> List[ResearchSource]:
        """Emergency search to reach minimum source count"""
        
        additional_sources = []
        
        # Try broader search terms
        broader_queries = [
            f"{query} information",
            f"{query} facts",
            f"{query} overview",
            query.split()[0] if ' ' in query else query  # First word only
        ]
        
        for broad_query in broader_queries:
            if len(additional_sources) >= needed_count:
                break
            
            try:
                if self.searcher.brave_api_key:
                    sources = await self.searcher._brave_search(broad_query, needed_count)
                    additional_sources.extend(sources)
            except Exception as e:
                self.logger.warning(f"Emergency search failed for {broad_query}: {e}")
        
        return additional_sources[:needed_count]
    
    async def _intelligent_source_selection(
        self, 
        sources: List[ResearchSource], 
        target_count: int
    ) -> List[ResearchSource]:
        """Intelligently select the best sources from a large pool"""
        
        # Score sources based on multiple factors
        scored_sources = []
        
        for source in sources:
            score = 0
            
            # Credibility score (already provided)
            score += source.credibility_score * 40
            
            # Source type priority
            type_scores = {
                'academic': 30,
                'government': 25,
                'news': 20,
                'organization': 15,
                'blog': 10,
                'social': 5
            }
            score += type_scores.get(source.source_type, 5)
            
            # Content length (more detailed content preferred)
            if len(source.content) > 1000:
                score += 15
            elif len(source.content) > 500:
                score += 10
            elif len(source.content) > 200:
                score += 5
            
            # Domain authority (simple heuristic)
            high_authority_domains = [
                'edu', 'gov', 'org', 'nature.com', 'science.org', 
                'ncbi.nlm.nih.gov', 'arxiv.org', 'reuters.com', 'bbc.com'
            ]
            
            if any(domain in source.domain.lower() for domain in high_authority_domains):
                score += 20
            
            scored_sources.append((source, score))
        
        # Sort by score and return top sources
        scored_sources.sort(key=lambda x: x[1], reverse=True)
        
        return [source for source, score in scored_sources[:target_count]]
    
    async def _synthesize_with_sequential_thinking(
        self, 
        query: str, 
        sources: List[ResearchSource], 
        thinking_context: Dict[str, Any]
    ) -> ResearchFindings:
        """Synthesize research with sequential thinking approach"""
        
        synthesis_prompt = f"""
        Using sequential thinking, synthesize comprehensive research findings for: "{query}"
        
        SOURCES ANALYZED: {len(sources)} high-quality sources
        
        SEQUENTIAL SYNTHESIS PROCESS:
        
        1. INFORMATION ANALYSIS:
        - Review all {len(sources)} sources systematically
        - Identify key facts, claims, and evidence
        - Note source credibility and types
        
        2. PATTERN RECOGNITION:
        - Find common themes and consensus points
        - Identify contradictions and debates
        - Recognize knowledge gaps or limitations
        
        3. CRITICAL EVALUATION:
        - Assess reliability of different claims
        - Evaluate strength of evidence
        - Consider potential biases or limitations
        
        4. SYNTHESIS CONSTRUCTION:
        - Integrate findings into coherent narrative
        - Present balanced view of the topic
        - Highlight key insights and implications
        
        5. CONFIDENCE ASSESSMENT:
        - Evaluate overall confidence in findings
        - Identify areas of certainty vs uncertainty
        - Provide confidence score (0-1)
        
        SOURCE DETAILS:
        {self._format_sources_for_analysis(sources)}
        
        Please provide:
        1. Comprehensive synthesis (detailed analysis)
        2. Key insights (3-7 main points)
        3. Any contradictions found
        4. Knowledge gaps identified
        5. Research recommendations
        6. Overall confidence score
        
        Use the sequential thinking process explicitly.
        """
        
        try:
            # Simple synthesis with thinking
            researcher = SimpleGeminiResearcher(self.google_api_key)
            response = await researcher.research_with_thinking(query, synthesis_prompt)
            
            # Parse the structured response
            findings = self._parse_synthesis_response(query, sources, response, thinking_context)
            
            return findings
            
        except Exception as e:
            self.logger.error(f"Sequential thinking synthesis failed: {e}")
            # Fall back to basic synthesis
            return await self.synthesizer.synthesize_research(query, sources)
    
    def _format_sources_for_analysis(self, sources: List[ResearchSource]) -> str:
        """Format sources for AI analysis"""
        
        formatted = []
        for i, source in enumerate(sources[:20], 1):  # Limit to first 20 for token efficiency
            formatted.append(
                f"{i}. [{source.source_type.upper()}] {source.title}\n"
                f"   Domain: {source.domain} | Credibility: {source.credibility_score:.2f}\n"
                f"   Content: {source.content[:300]}...\n"
            )
        
        if len(sources) > 20:
            formatted.append(f"\n... and {len(sources) - 20} additional sources")
        
        return "\n".join(formatted)
    
    def _parse_synthesis_response(
        self, 
        query: str, 
        sources: List[ResearchSource], 
        response: str, 
        thinking_context: Dict[str, Any]
    ) -> ResearchFindings:
        """Parse the AI synthesis response into structured findings"""
        
        try:
            # Extract key components from the response
            lines = response.split('\n')
            
            synthesis = response  # Use full response as synthesis
            key_insights = []
            contradictions = []
            gaps = []
            recommendations = []
            confidence_score = 0.8  # Default
            
            # Simple parsing logic (could be enhanced)
            current_section = None
            for line in lines:
                line = line.strip()
                if 'key insights' in line.lower():
                    current_section = 'insights'
                elif 'contradictions' in line.lower():
                    current_section = 'contradictions'
                elif 'gaps' in line.lower():
                    current_section = 'gaps'
                elif 'recommendations' in line.lower():
                    current_section = 'recommendations'
                elif 'confidence' in line.lower():
                    # Try to extract confidence score
                    import re
                    score_match = re.search(r'(0\.[0-9]+|[0-1]\.[0-9]+)', line)
                    if score_match:
                        confidence_score = float(score_match.group(1))
                elif line.startswith(('-', '•', '*')) and current_section:
                    content = line[1:].strip()
                    if current_section == 'insights':
                        key_insights.append(content)
                    elif current_section == 'contradictions':
                        contradictions.append(content)
                    elif current_section == 'gaps':
                        gaps.append(content)
                    elif current_section == 'recommendations':
                        recommendations.append(content)
            
            return ResearchFindings(
                query=query,
                sources=sources,
                synthesis=synthesis,
                confidence_score=confidence_score,
                key_insights=key_insights or ["Comprehensive analysis completed"],
                contradictions=contradictions or [],
                gaps=gaps or [],
                recommendations=recommendations or ["Continue monitoring for new developments"],
                timestamp=time.time()
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing synthesis response: {e}")
            
            # Return basic findings structure
            return ResearchFindings(
                query=query,
                sources=sources,
                synthesis=response,
                confidence_score=0.7,
                key_insights=["Analysis completed with sequential thinking"],
                contradictions=[],
                gaps=[],
                recommendations=["Review sources for additional insights"],
                timestamp=time.time()
            )
    
    async def conduct_comprehensive_research(
        self, 
        query: str, 
        max_sources: int = 100, 
        use_sequential_thinking: bool = True
    ) -> ResearchFindings:
        """Conduct comprehensive multi-source research using ALL available sources"""
        
        # Check cache first
        cache_key = hashlib.md5(query.encode()).hexdigest()
        if cache_key in self.research_cache:
            cached_result = self.research_cache[cache_key]
            if time.time() - cached_result.timestamp < 3600:  # 1 hour cache
                self.logger.info(f"📋 Returning cached research for: {query}")
                return cached_result
        
        self.logger.info(f"🔍 Starting comprehensive research for: {query}")
        
        try:
            # Initialize sequential thinking if enabled
            if use_sequential_thinking:
                thinking_context = await self._initialize_research_thinking(query)
                self.logger.info(f"🧠 Sequential thinking initialized for research")
            
            # Step 1: Comprehensive multi-source search (up to max_sources)
            sources = await self._comprehensive_multi_source_search(query, max_sources)
            self.logger.info(f"📚 Found {len(sources)} sources from comprehensive search")
            
            # Step 2: Use ALL found sources (no artificial limits)
            # Prioritize sources by quality but don't limit quantity
            if len(sources) > 50:
                # For large source sets, rank by quality but keep all
                selected_sources = await self._intelligent_source_selection(sources, len(sources))
                self.logger.info(f"🎯 Using all {len(selected_sources)} sources (quality ranked)")
            else:
                selected_sources = sources  # Use all available sources
                self.logger.info(f"🎯 Using all {len(selected_sources)} available sources")
            
            # Step 3: Extract full content from selected sources
            extracted_sources = await self.extractor.extract_full_content(selected_sources)
            self.logger.info(f"📄 Extracted content from {len(extracted_sources)} sources")
            
            # Step 4: Apply sequential thinking to research synthesis
            if use_sequential_thinking:
                findings = await self._synthesize_with_sequential_thinking(
                    query, extracted_sources, thinking_context
                )
            else:
                findings = await self.synthesizer.synthesize_research(query, extracted_sources)
            
            # Cache the results
            self.research_cache[cache_key] = findings
            
            self.logger.info(f"✅ Comprehensive research completed for: {query}")
            
            return findings
            
        except Exception as e:
            self.logger.error(f"❌ Research failed for query '{query}': {e}")
            raise
    
    async def fact_check_claim(self, claim: str) -> Dict[str, Any]:
        """Fact-check a specific claim using multiple sources"""
        
        self.logger.info(f"🔍 Fact-checking claim: {claim}")
        
        # Conduct research on the claim
        findings = await self.conduct_comprehensive_research(f"fact check: {claim}")
        
        # Create fact-check specific analysis
        fact_check_prompt = f"""
        Conduct a thorough fact-check analysis for the following claim:
        
        CLAIM: "{claim}"
        
        Based on the research findings provided, determine:
        
        1. VERDICT: True, False, Partially True, or Insufficient Evidence
        2. EVIDENCE QUALITY: Rate the quality of available evidence (1-5)
        3. SOURCE RELIABILITY: Assess the reliability of sources
        4. SUPPORTING EVIDENCE: List evidence that supports the claim
        5. CONTRADICTING EVIDENCE: List evidence that contradicts the claim
        6. CONTEXT AND NUANCE: Provide important context or nuance
        7. CONFIDENCE LEVEL: Your confidence in the verdict (0.0-1.0)
        
        Research findings:
        {findings.synthesis}
        
        Sources analyzed: {len(findings.sources)}
        Overall research confidence: {findings.confidence_score}
        
        Provide a clear, evidence-based fact-check analysis.
        """
        
        fact_check_result = await self.gemini_manager.deep_think_reasoning(
            fact_check_prompt,
            thinking_budget=1024,
            enable_parallel_thinking=True
        )
        
        return {
            'claim': claim,
            'verdict': self._extract_verdict(fact_check_result['thinking_process']),
            'evidence_quality': self._extract_quality_score(fact_check_result['thinking_process']),
            'confidence': fact_check_result['confidence_score'],
            'analysis': fact_check_result['thinking_process'],
            'sources_count': len(findings.sources),
            'research_findings': findings,
            'timestamp': time.time()
        }
    
    def _extract_verdict(self, text: str) -> str:
        """Extract verdict from fact-check analysis"""
        text_lower = text.lower()
        
        if 'verdict: true' in text_lower or 'verdict is true' in text_lower:
            return 'True'
        elif 'verdict: false' in text_lower or 'verdict is false' in text_lower:
            return 'False'
        elif 'partially true' in text_lower:
            return 'Partially True'
        elif 'insufficient evidence' in text_lower:
            return 'Insufficient Evidence'
        else:
            return 'Unclear'
    
    def _extract_quality_score(self, text: str) -> int:
        """Extract evidence quality score from analysis"""
        import re
        
        # Look for patterns like "quality: 4" or "evidence quality: 3"
        quality_match = re.search(r'quality.*?(\d)', text.lower())
        if quality_match:
            return int(quality_match.group(1))
        
        return 3  # Default moderate quality
    
    async def comparative_analysis(self, topics: List[str]) -> Dict[str, Any]:
        """Conduct comparative analysis across multiple topics"""
        
        self.logger.info(f"📊 Conducting comparative analysis for {len(topics)} topics")
        
        # Research each topic
        research_tasks = []
        for topic in topics:
            research_tasks.append(self.conduct_comprehensive_research(topic))
        
        all_findings = await asyncio.gather(*research_tasks)
        
        # Create comparative analysis
        comparison_prompt = f"""
        Conduct a comprehensive comparative analysis across the following topics:
        
        Topics: {', '.join(topics)}
        
        For each topic, I have conducted detailed research. Now provide:
        
        1. COMPARATIVE OVERVIEW
           - Key similarities across topics
           - Major differences and distinctions
           - Unique aspects of each topic
        
        2. CROSS-TOPIC INSIGHTS
           - Patterns that emerge across topics
           - Interconnections and relationships
           - Synthesis of findings
        
        3. EVIDENCE STRENGTH COMPARISON
           - Which topics have strongest evidence base
           - Areas where evidence is conflicting or weak
           - Reliability comparison across topics
        
        4. PRACTICAL IMPLICATIONS
           - How findings relate to real-world applications
           - Decision-making guidance based on comparison
           - Action recommendations
        
        Research findings for each topic:
        {json.dumps([{'topic': topics[i], 'summary': findings.synthesis[:500]} for i, findings in enumerate(all_findings)], indent=2)}
        
        Provide a thorough comparative analysis that identifies patterns, contrasts, and synthesis across all topics.
        """
        
        comparison_result = await self.gemini_manager.deep_think_reasoning(
            comparison_prompt,
            thinking_budget=-1,
            enable_parallel_thinking=True
        )
        
        return {
            'topics': topics,
            'comparative_analysis': comparison_result['thinking_process'],
            'individual_findings': {topics[i]: findings for i, findings in enumerate(all_findings)},
            'confidence_score': comparison_result['confidence_score'],
            'cross_topic_insights': comparison_result.get('reasoning_chains', []),
            'timestamp': time.time()
        }
    
    def get_research_cache_stats(self) -> Dict[str, Any]:
        """Get research cache statistics"""
        return {
            'cached_queries': len(self.research_cache),
            'cache_size_mb': sum(len(str(findings)) for findings in self.research_cache.values()) / (1024 * 1024),
            'oldest_cache_age': min((time.time() - findings.timestamp) / 3600 for findings in self.research_cache.values()) if self.research_cache else 0
        }
    
    def clear_cache(self):
        """Clear research cache"""
        self.research_cache.clear()
        self.logger.info("🧹 Research cache cleared")