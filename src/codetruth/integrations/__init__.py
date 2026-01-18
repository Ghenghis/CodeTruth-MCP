"""
Integrations Module

Provides integrations with:
- LM Studio (local AI models)
- Ollama (local LLM inference)
- Windsurf IDE
- VS Code
- Mem0 AI Memory
- Supabase (local)
"""

from codetruth.integrations.lm_studio import LMStudioClient
from codetruth.integrations.ollama import OllamaClient
from codetruth.integrations.windsurf import WindsurfIntegration
from codetruth.integrations.mem0_integration import Mem0Integration
from codetruth.integrations.supabase_local import SupabaseLocalClient

__all__ = [
    "LMStudioClient",
    "OllamaClient",
    "WindsurfIntegration",
    "Mem0Integration",
    "SupabaseLocalClient",
]
