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
    
    async def multi_source_search(self, query: str, max_results: int = 20) -> List[ResearchSource]:
        """Perform search across multiple sources and engines"""
        
        all_sources = []
        
        # Search tasks to run in parallel
        search_tasks = []
        
        # General web search
        if self.brave_api_key:
            search_tasks.append(self._brave_search(query, max_results // 4))
        
        # Academic search
        search_tasks.append(self._academic_search(query, max_results // 4))
        
        # News search
        search_tasks.append(self._news_search(query, max_results // 4))
        
        # Specialized search (government, organizations)
        search_tasks.append(self._specialized_search(query, max_results // 4))
        
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
            params = {"q": query, "count": max_results}
            
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
            params = {
                'search_query': f'all:{query}',
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
            params = {
                'query': query,
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
            
            # Relevance based on title and content
            title_matches = sum(1 for term in query_terms if term in source.title.lower())
            content_matches = sum(1 for term in query_terms if term in source.content.lower())
            
            relevance_score = (title_matches * 2 + content_matches) / (len(query_terms) * 3)
            score += relevance_score * 0.5
            
            # Boost for citations (if available)
            if source.citations > 0:
                score += min(source.citations / 100, 0.2)  # Cap at 0.2 boost
            
            # Boost for academic sources
            if source.source_type == "academic":
                score += 0.1
            
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


class ResearchSynthesizer:
    """Synthesize research findings from multiple sources"""
    
    def __init__(self, gemini_manager):
        self.gemini_manager = gemini_manager
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
        
        # Get synthesis from Gemini
        synthesis_result = await self.gemini_manager.deep_think_reasoning(
            synthesis_prompt,
            thinking_budget=-1,  # Dynamic thinking for complex analysis
            enable_parallel_thinking=True
        )
        
        # Extract structured information from synthesis
        synthesis_text = synthesis_result['thinking_process']
        
        findings = ResearchFindings(
            query=query,
            sources=sources,
            synthesis=synthesis_text,
            confidence_score=synthesis_result['confidence_score'],
            key_insights=self._extract_insights(synthesis_text),
            contradictions=self._extract_contradictions(synthesis_text),
            gaps=self._extract_gaps(synthesis_text),
            recommendations=self._extract_recommendations(synthesis_text),
            timestamp=time.time()
        )
        
        self.logger.info(f"✅ Research synthesis completed with {len(findings.key_insights)} insights")
        
        return findings
    
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
    """Main manager for enhanced research capabilities"""
    
    def __init__(self, gemini_manager, brave_api_key: str = None, serpapi_key: str = None):
        self.gemini_manager = gemini_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.searcher = AdvancedWebSearcher(brave_api_key, serpapi_key)
        self.extractor = ContentExtractor()
        self.synthesizer = ResearchSynthesizer(gemini_manager)
        
        # Research cache
        self.research_cache = {}
        
        self.logger.info("🔬 Enhanced Research Manager initialized")
    
    async def conduct_comprehensive_research(self, query: str, max_sources: int = 15) -> ResearchFindings:
        """Conduct comprehensive multi-source research"""
        
        # Check cache first
        cache_key = hashlib.md5(query.encode()).hexdigest()
        if cache_key in self.research_cache:
            cached_result = self.research_cache[cache_key]
            if time.time() - cached_result.timestamp < 3600:  # 1 hour cache
                self.logger.info(f"📋 Returning cached research for: {query}")
                return cached_result
        
        self.logger.info(f"🔍 Starting comprehensive research for: {query}")
        
        try:
            # Step 1: Multi-source search
            sources = await self.searcher.multi_source_search(query, max_sources)
            self.logger.info(f"📚 Found {len(sources)} initial sources")
            
            # Step 2: Extract full content from top sources
            top_sources = sources[:10]  # Limit content extraction to top 10
            extracted_sources = await self.extractor.extract_full_content(top_sources)
            self.logger.info(f"📄 Extracted content from {len(extracted_sources)} sources")
            
            # Step 3: Synthesize research findings
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