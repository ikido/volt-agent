"""OpenAI LLM client for generating summaries"""

import logging
from typing import Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for OpenAI API"""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview",
                 max_tokens: int = 4000, temperature: float = 0.3,
                 timeout: int = 60):
        """Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key
            model: Model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            timeout: Request timeout in seconds
        """
        self.client = OpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate completion using OpenAI API (generic method)
        
        Args:
            prompt: Prompt text
            system_prompt: Optional system prompt (defaults to time tracking expert)
            
        Returns:
            Generated text
        """
        if system_prompt is None:
            system_prompt = "You are an expert at analyzing time tracking data and project management information."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            result = response.choices[0].message.content
            
            # Log token usage
            usage = response.usage
            logger.info(f"LLM API call - Tokens: {usage.total_tokens} "
                       f"(prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")
            
            return result
            
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            return f"[Error generating summary: {str(e)}]"
    
    def generate_summary(self, prompt: str) -> str:
        """Generate summary using OpenAI API (convenience wrapper)
        
        Args:
            prompt: Prompt text
            
        Returns:
            Generated text
        """
        return self.generate_completion(prompt)
    
    def generate_matched_summary(self, entries_text: str) -> str:
        """Generate summary for matched entities
        
        Args:
            entries_text: Formatted text of matched time entries
            
        Returns:
            Generated summary
        """
        prompt = f"""You are analyzing time tracking data. Below are time entries matched to project entities.

Your task: Create a list where each entity gets ONE short, concise sentence about what was done.

Format EXACTLY like this for EACH entity:
- **#[ID] [[Database]] [[Type]] [[Project]]**: One short sentence about what was accomplished. ([X.X] hours)

Rules:
- One line per entity
- Keep sentences SHORT and factual
- No fluff or made-up details
- Only describe what's in the description
- List ALL entities

Time entries:
{entries_text}

Generate the list now:"""
        
        return self.generate_summary(prompt)
    
    def generate_unmatched_summary(self, entries_text: str) -> str:
        """Generate summary for unmatched entities
        
        Args:
            entries_text: Formatted text of unmatched time entries
            
        Returns:
            Generated summary
        """
        prompt = f"""You are analyzing untracked time entries (meetings, admin tasks, etc).

Your task: Create a bullet list where each activity type gets ONE short sentence.

Format:
- **[Activity name]**: One short sentence. ([X.X] hours)

Rules:
- Group similar activities together
- Keep sentences SHORT and factual
- List ALL activities
- No fluff

Time entries:
{entries_text}

Generate the bullet list now:"""
        
        return self.generate_summary(prompt)
    
    def generate_team_summary(self, individual_reports: str, start_date: str, end_date: str) -> str:
        """Generate team-level summary
        
        Args:
            individual_reports: Combined individual report text
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Generated team summary
        """
        prompt = f"""You are creating a comprehensive team activity report based on individual team member reports.

Below are the individual activity summaries for each team member for the period 
{start_date} to {end_date}.

Your task is to synthesize this information into a cohesive team report that:
1. Provides an executive summary of team activities
2. Identifies major focus areas and projects worked on
3. Highlights patterns in how time was distributed
4. Notes any areas that received significant team attention
5. Identifies any gaps or unusual patterns

IMPORTANT: Ensure the report is comprehensive and captures all major activities across 
the team. Do not omit significant projects or focus areas.

Individual Reports:
{individual_reports}

Generate the team summary now:"""
        
        return self.generate_summary(prompt)

