"""
AI Provider abstraction layer for workout recommendations.
Supports multiple AI providers (OpenAI, Claude/Anthropic).
"""

import os
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import openai
import anthropic
from dotenv import load_dotenv

load_dotenv()


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def generate_completion(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate a completion from the AI provider"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is properly configured and available"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the provider"""
        pass
    
    @abstractmethod
    def get_error_message(self) -> str:
        """Get configuration error message if provider is not available"""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider implementation"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4o"
        self.fallback_model = "gpt-4o-mini"
        self.client = None
        self.error_message = ""
        
        if self.api_key and self.api_key != "your_openai_api_key_here":
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
            except Exception as e:
                self.error_message = f"Failed to initialize OpenAI client: {str(e)}"
        else:
            self.error_message = "OpenAI API key not configured in .env file"
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def get_provider_name(self) -> str:
        return "OpenAI"
    
    def get_error_message(self) -> str:
        return self.error_message
    
    def generate_completion(self, prompt: str, temperature: float = 0.7) -> str:
        if not self.client:
            raise ValueError(self.error_message)
        
        try:
            # Try primary model first
            response = self._call_model(self.model, prompt, temperature)
            return response
        except Exception as e:
            if "model" in str(e).lower() or "rate" in str(e).lower():
                # Try fallback model
                print(f"Primary model failed ({e}), trying fallback model...")
                response = self._call_model(self.fallback_model, prompt, temperature)
                return response
            else:
                raise
    
    def _call_model(self, model: str, prompt: str, temperature: float) -> str:
        try:
            print(f"🔍 Calling OpenAI model: {model}")
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert fitness coach specializing in polarized training for endurance athletes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            
            if not response.choices or not response.choices[0].message:
                raise ValueError("OpenAI returned no message content")
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ OpenAI API error: {type(e).__name__}: {str(e)}")
            raise


class ClaudeProvider(AIProvider):
    """Anthropic Claude provider implementation"""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = "claude-3-opus-20240229"  # Opus 4 model
        self.fallback_model = "claude-3-5-sonnet-20241022"  # Sonnet fallback (if needed)
        self.client = None
        self.error_message = ""
        
        if self.api_key and self.api_key != "your_anthropic_api_key_here":
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                self.error_message = f"Failed to initialize Claude client: {str(e)}"
        else:
            self.error_message = "Anthropic API key not configured in .env file"
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def get_provider_name(self) -> str:
        return "Claude Opus 4"
    
    def get_error_message(self) -> str:
        return self.error_message
    
    def generate_completion(self, prompt: str, temperature: float = 0.7) -> str:
        if not self.client:
            raise ValueError(self.error_message)
        
        # Claude requires explicit JSON instruction in the prompt
        json_prompt = prompt + "\n\nIMPORTANT: Return your response as a valid JSON object only, with no additional text or markdown formatting."
        
        # Try primary model (Opus 4) first
        try:
            return self._call_model(self.model, json_prompt, temperature)
        except Exception as e:
            # Check if we should try fallback model
            error_str = str(e).lower()
            if "model" in error_str or "not available" in error_str or "rate" in error_str:
                print(f"Primary Claude model failed ({e}), trying fallback model...")
                try:
                    return self._call_model(self.fallback_model, json_prompt, temperature)
                except Exception as fallback_e:
                    print(f"❌ Claude fallback model also failed: {fallback_e}")
                    raise fallback_e
            else:
                raise
        
    
    def _call_model(self, model: str, json_prompt: str, temperature: float) -> str:
        try:
            print(f"🔍 Calling Claude model: {model}")
            response = self.client.messages.create(
                model=model,
                max_tokens=4000,
                temperature=temperature,
                system="You are an expert fitness coach specializing in polarized training for endurance athletes. Always respond with valid JSON.",
                messages=[
                    {"role": "user", "content": json_prompt}
                ]
            )
            
            if not response.content:
                raise ValueError("Claude returned no content")
            
            # Extract text from Claude's response
            content = response.content[0].text if isinstance(response.content, list) else response.content
            
            # Claude sometimes adds markdown formatting, strip it
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # Validate it's proper JSON
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Claude did not return valid JSON: {e}")
            
            return content
        except Exception as e:
            print(f"❌ Claude API error with {model}: {type(e).__name__}: {str(e)}")
            raise


class AIProviderManager:
    """Enhanced provider management with fallback and status reporting"""
    
    def __init__(self, status_callback=None):
        """
        Initialize provider manager.
        
        Args:
            status_callback: Function to call with status updates (message: str)
        """
        self.status_callback = status_callback or (lambda msg: print(f"📝 {msg}"))
        self.providers = []
        self.current_provider_index = 0
        
        # Initialize providers in order: Claude Opus 4 → OpenAI
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers in fallback order"""
        provider_configs = [
            ("Claude Opus 4", ClaudeProvider),
            ("OpenAI GPT-4o", OpenAIProvider)
        ]
        
        for name, provider_class in provider_configs:
            try:
                provider = provider_class()
                if provider.is_available():
                    self.providers.append((name, provider))
                    self.status_callback(f"✅ {name} configured and available")
                else:
                    self.status_callback(f"❌ {name} not available: {provider.get_error_message()}")
            except Exception as e:
                self.status_callback(f"❌ Failed to initialize {name}: {str(e)}")
        
        if not self.providers:
            raise ValueError("No AI providers available. Please check your API keys in .env file.")
        
        self.status_callback(f"📋 Total available providers: {len(self.providers)}")
    
    def generate_with_fallback(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate completion with automatic fallback"""
        if not self.providers:
            raise ValueError("No providers available")
        
        last_error = None
        
        for i, (name, provider) in enumerate(self.providers):
            try:
                self.status_callback(f"🔍 Trying {name}...")
                
                # Call the provider
                result = provider.generate_completion(prompt, temperature)
                
                self.status_callback(f"✅ {name} succeeded")
                return result
                
            except Exception as e:
                error_str = str(e)
                self.status_callback(f"❌ {name} failed: {error_str}")
                last_error = e
                
                # If this isn't the last provider, try fallback
                if i < len(self.providers) - 1:
                    next_name = self.providers[i + 1][0]
                    self.status_callback(f"🔄 Falling back to {next_name}...")
                    continue
                else:
                    # Last provider failed
                    self.status_callback(f"❌ All providers failed")
                    break
        
        # If we get here, all providers failed
        if last_error:
            raise last_error
        else:
            raise ValueError("All AI providers failed")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return [name for name, _ in self.providers]
    
    def get_current_provider_name(self) -> str:
        """Get name of the provider that would be tried first"""
        if self.providers:
            return self.providers[0][0]
        return "None"


class AIProviderFactory:
    """Factory class to create AI providers based on configuration (legacy compatibility)"""
    
    @staticmethod
    def create_provider(provider_name: Optional[str] = None) -> AIProvider:
        """
        Create an AI provider instance.
        
        Args:
            provider_name: Name of the provider ('openai', 'claude', or None for auto-detect)
            
        Returns:
            AIProvider instance
            
        Raises:
            ValueError if no provider is available
        """
        if provider_name is None:
            provider_name = os.getenv("AI_PROVIDER", "auto").lower()
        
        provider_name = provider_name.lower()
        
        if provider_name == "openai":
            provider = OpenAIProvider()
            if provider.is_available():
                print(f"✅ Using OpenAI for AI recommendations")
                return provider
            else:
                raise ValueError(f"OpenAI provider not available: {provider.get_error_message()}")
        
        elif provider_name == "claude" or provider_name == "anthropic":
            provider = ClaudeProvider()
            if provider.is_available():
                print(f"✅ Using Claude for AI recommendations")
                return provider
            else:
                raise ValueError(f"Claude provider not available: {provider.get_error_message()}")
        
        elif provider_name == "auto":
            # Try providers in order of preference
            providers = [
                ("Claude", ClaudeProvider),
                ("OpenAI", OpenAIProvider)
            ]
            
            for name, provider_class in providers:
                try:
                    provider = provider_class()
                    if provider.is_available():
                        print(f"✅ Auto-detected {name} for AI recommendations")
                        return provider
                except Exception:
                    continue
            
            # No provider available, collect error messages
            error_messages = []
            for name, provider_class in providers:
                provider = provider_class()
                if not provider.is_available():
                    error_messages.append(f"{name}: {provider.get_error_message()}")
            
            raise ValueError(
                "No AI provider available. Configure at least one provider:\n" + 
                "\n".join(f"  - {msg}" for msg in error_messages)
            )
        
        else:
            raise ValueError(f"Unknown AI provider: {provider_name}. Use 'openai', 'claude', or 'auto'")
    
    @staticmethod
    def create_manager(status_callback=None) -> AIProviderManager:
        """Create a provider manager with fallback support"""
        return AIProviderManager(status_callback)