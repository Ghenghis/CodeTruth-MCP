"""
UI No-Op Verifier Engine

Detects UI elements that appear functional but do nothing.
This includes:
- Buttons with empty handlers
- Handlers that only log
- Forms that don't submit
- Links that don't navigate
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class UIElementType(Enum):
    """Types of interactive UI elements."""
    BUTTON = "button"
    LINK = "link"
    FORM = "form"
    INPUT = "input"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    MENU_ITEM = "menu_item"
    TAB = "tab"
    MODAL_TRIGGER = "modal_trigger"


class EffectType(Enum):
    """Types of observable effects."""
    NETWORK_CALL = "network_call"       # fetch, axios, API call
    DOM_MUTATION = "dom_mutation"       # State change, DOM update
    NAVIGATION = "navigation"           # URL change, redirect
    STORAGE = "storage"                 # localStorage, sessionStorage
    CONSOLE = "console"                 # console.log (not a real effect)
    STATE_CHANGE = "state_change"       # React state, Redux, etc.
    CALLBACK = "callback"               # Callback invocation
    NONE = "none"                       # No observable effect


class NoOpReason(Enum):
    """Reasons why a UI element is a no-op."""
    EMPTY_HANDLER = "empty_handler"             # Handler body is empty
    DEBUG_ONLY = "debug_only"                   # Only console.log
    HANDLER_NOT_BOUND = "handler_not_bound"     # Handler defined but not used
    HANDLER_UNDEFINED = "handler_undefined"     # Handler referenced but not defined
    DISABLED = "disabled"                       # Element is disabled
    PREVENTED = "prevented"                     # Event prevented, no follow-through
    CONDITIONAL_NEVER = "conditional_never"     # Condition always false
    ASYNC_VOID = "async_void"                   # Async but no await/then


@dataclass
class UIElement:
    """Represents an interactive UI element."""
    element_id: str
    element_type: UIElementType
    location: Dict[str, Any]
    text_content: Optional[str] = None
    handler_name: Optional[str] = None
    handler_location: Optional[Dict[str, Any]] = None
    attributes: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.element_id,
            "type": self.element_type.value,
            "location": self.location,
            "text": self.text_content,
            "handler": self.handler_name,
            "handler_location": self.handler_location,
            "attributes": self.attributes,
        }


@dataclass
class NoOpFinding:
    """A finding of a UI element that does nothing."""
    finding_id: str
    element: UIElement
    reason: NoOpReason
    severity: str  # "critical", "high", "medium", "low"
    confidence: float
    explanation: str
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    suggested_fix: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "type": "NO_OP_UI",
            "element": self.element.to_dict(),
            "reason": self.reason.value,
            "severity": self.severity,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "evidence": self.evidence,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class UIVerificationReport:
    """Complete UI verification report."""
    repo_path: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    total_elements: int = 0
    no_op_count: int = 0
    findings: List[NoOpFinding] = field(default_factory=list)
    elements_analyzed: List[UIElement] = field(default_factory=list)
    blindspots: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": "1.0.0",
            "repo_path": self.repo_path,
            "created_at": self.created_at.isoformat(),
            "statistics": {
                "total_elements": self.total_elements,
                "no_op_count": self.no_op_count,
                "no_op_percentage": round(
                    (self.no_op_count / max(self.total_elements, 1)) * 100, 2
                ),
            },
            "findings": [f.to_dict() for f in self.findings],
            "elements": [e.to_dict() for e in self.elements_analyzed],
            "blindspots": self.blindspots,
        }

    def export_json(self, output_path: Path) -> None:
        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class UIVerifier:
    """
    Verifies that UI elements have real effects.

    Static analysis approach:
    1. Find all interactive elements (buttons, links, forms)
    2. Trace their handlers
    3. Analyze handler bodies for effects
    4. Report elements with no observable effects
    """

    STANDARD_BLINDSPOTS = [
        "Dynamic handler assignment (handler set at runtime)",
        "Handlers in external libraries",
        "Effects via Redux/MobX/Zustand actions",
        "Effects via Context API",
        "Async effects that happen after handler returns",
        "Server-side effects (SSR)",
    ]

    # Patterns for detecting interactive elements
    ELEMENT_PATTERNS = {
        "button": re.compile(
            r"<button[^>]*>([^<]*)</button>|<Button[^>]*>([^<]*)</Button>",
            re.IGNORECASE | re.DOTALL
        ),
        "button_role": re.compile(
            r'role\s*=\s*["\']button["\']',
            re.IGNORECASE
        ),
        "click_handler": re.compile(
            r'onClick\s*=\s*\{?\s*(\w+)',
            re.IGNORECASE
        ),
        "submit_handler": re.compile(
            r'onSubmit\s*=\s*\{?\s*(\w+)',
            re.IGNORECASE
        ),
        "form": re.compile(
            r'<form[^>]*>',
            re.IGNORECASE
        ),
        "link": re.compile(
            r'<a\s+[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>',
            re.IGNORECASE
        ),
    }

    # Patterns for detecting effects in handler bodies
    EFFECT_PATTERNS = {
        EffectType.NETWORK_CALL: [
            re.compile(r'\bfetch\s*\('),
            re.compile(r'\baxios\s*\.\s*\w+\s*\('),
            re.compile(r'\bapi\s*\.\s*\w+\s*\(', re.IGNORECASE),
            re.compile(r'\.post\s*\('),
            re.compile(r'\.get\s*\('),
            re.compile(r'\.put\s*\('),
            re.compile(r'\.delete\s*\('),
            re.compile(r'useMutation'),
            re.compile(r'useQuery'),
        ],
        EffectType.STATE_CHANGE: [
            re.compile(r'\bset[A-Z]\w*\s*\('),  # setState pattern
            re.compile(r'\.setState\s*\('),
            re.compile(r'dispatch\s*\('),
            re.compile(r'\.dispatch\s*\('),
            re.compile(r'store\.\w+\s*='),
        ],
        EffectType.NAVIGATION: [
            re.compile(r'navigate\s*\('),
            re.compile(r'router\s*\.\s*push\s*\('),
            re.compile(r'router\s*\.\s*replace\s*\('),
            re.compile(r'history\s*\.\s*push\s*\('),
            re.compile(r'window\.location'),
            re.compile(r'redirect\s*\('),
        ],
        EffectType.STORAGE: [
            re.compile(r'localStorage\s*\.'),
            re.compile(r'sessionStorage\s*\.'),
            re.compile(r'cookies\s*\.'),
        ],
        EffectType.DOM_MUTATION: [
            re.compile(r'\.innerHTML\s*='),
            re.compile(r'\.textContent\s*='),
            re.compile(r'\.appendChild\s*\('),
            re.compile(r'\.removeChild\s*\('),
            re.compile(r'document\.createElement'),
        ],
        EffectType.CALLBACK: [
            re.compile(r'on\w+\s*\('),  # onSuccess, onError, etc.
            re.compile(r'callback\s*\('),
            re.compile(r'props\.\w+\s*\('),
        ],
        EffectType.CONSOLE: [
            re.compile(r'console\s*\.\s*\w+\s*\('),
        ],
    }

    def __init__(self):
        self._finding_counter = 0
        self._element_counter = 0

    def _generate_finding_id(self) -> str:
        self._finding_counter += 1
        return f"noop_{self._finding_counter:06d}"

    def _generate_element_id(self) -> str:
        self._element_counter += 1
        return f"elem_{self._element_counter:06d}"

    def verify_directory(self, directory: Path) -> UIVerificationReport:
        """
        Verify all UI files in a directory.
        """
        report = UIVerificationReport(repo_path=str(directory))
        report.blindspots = self.STANDARD_BLINDSPOTS

        # Find all React/Vue files
        patterns = ["**/*.tsx", "**/*.jsx", "**/*.vue"]
        files: List[Path] = []
        for pattern in patterns:
            files.extend(directory.glob(pattern))

        # Exclude node_modules
        files = [f for f in files if "node_modules" not in str(f)]

        # Analyze each file
        for file_path in files:
            self._analyze_file(file_path, report)

        report.total_elements = len(report.elements_analyzed)
        report.no_op_count = len(report.findings)

        return report

    def verify_file(self, file_path: Path) -> UIVerificationReport:
        """
        Verify a single file.
        """
        report = UIVerificationReport(repo_path=str(file_path.parent))
        report.blindspots = self.STANDARD_BLINDSPOTS

        self._analyze_file(file_path, report)

        report.total_elements = len(report.elements_analyzed)
        report.no_op_count = len(report.findings)

        return report

    def _analyze_file(self, file_path: Path, report: UIVerificationReport) -> None:
        """
        Analyze a single file for no-op UI elements.
        """
        try:
            content = file_path.read_text(errors="ignore")
        except Exception:
            return

        rel_path = str(file_path)

        # Find all handlers defined in this file
        handlers = self._find_handlers(content, rel_path)

        # Find all interactive elements
        elements = self._find_interactive_elements(content, rel_path)

        for element in elements:
            report.elements_analyzed.append(element)

            # Check if element has a handler
            if element.handler_name:
                handler_body = handlers.get(element.handler_name)

                if handler_body is None:
                    # Handler referenced but not defined
                    finding = NoOpFinding(
                        finding_id=self._generate_finding_id(),
                        element=element,
                        reason=NoOpReason.HANDLER_UNDEFINED,
                        severity="high",
                        confidence=0.95,
                        explanation=f"Handler '{element.handler_name}' is referenced but not defined in this file.",
                        evidence=[{
                            "type": "missing_handler",
                            "handler_name": element.handler_name,
                            "location": element.location,
                        }],
                        suggested_fix=f"Define the handler: const {element.handler_name} = () => {{ /* implementation */ }}",
                    )
                    report.findings.append(finding)
                else:
                    # Analyze handler body
                    effects = self._analyze_handler_effects(handler_body)

                    if effects == {EffectType.NONE}:
                        finding = NoOpFinding(
                            finding_id=self._generate_finding_id(),
                            element=element,
                            reason=NoOpReason.EMPTY_HANDLER,
                            severity="critical",
                            confidence=0.98,
                            explanation=f"Handler '{element.handler_name}' has no observable effects. The function body is empty or only contains comments.",
                            evidence=[{
                                "type": "empty_handler",
                                "handler_name": element.handler_name,
                                "handler_body": handler_body[:200],
                                "location": element.handler_location,
                            }],
                            suggested_fix=f"Add functionality to {element.handler_name}, or remove the element if it's not needed.",
                        )
                        report.findings.append(finding)

                    elif effects == {EffectType.CONSOLE}:
                        finding = NoOpFinding(
                            finding_id=self._generate_finding_id(),
                            element=element,
                            reason=NoOpReason.DEBUG_ONLY,
                            severity="high",
                            confidence=0.95,
                            explanation=f"Handler '{element.handler_name}' only contains console.log statements. This is likely debug code that has no user-visible effect.",
                            evidence=[{
                                "type": "debug_only_handler",
                                "handler_name": element.handler_name,
                                "handler_body": handler_body[:200],
                                "detected_effects": ["console"],
                            }],
                            suggested_fix=f"Add real functionality to {element.handler_name}, or remove the debug logging.",
                        )
                        report.findings.append(finding)
            else:
                # Element without handler
                if element.element_type == UIElementType.BUTTON:
                    finding = NoOpFinding(
                        finding_id=self._generate_finding_id(),
                        element=element,
                        reason=NoOpReason.HANDLER_NOT_BOUND,
                        severity="critical",
                        confidence=0.90,
                        explanation=f"Button '{element.text_content or 'unnamed'}' has no onClick handler.",
                        evidence=[{
                            "type": "unbound_element",
                            "element_type": "button",
                            "location": element.location,
                        }],
                        suggested_fix="Add an onClick handler: onClick={handleClick}",
                    )
                    report.findings.append(finding)

    def _find_handlers(self, content: str, file_path: str) -> Dict[str, str]:
        """
        Find all handler definitions in a file.

        Returns a dict of handler_name -> handler_body
        """
        handlers: Dict[str, str] = {}

        # Pattern for handler definitions
        handler_patterns = [
            # const handleClick = () => { ... }
            re.compile(r'(?:const|let|var)\s+(handle\w+|on\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', re.DOTALL),
            # const handleClick = function() { ... }
            re.compile(r'(?:const|let|var)\s+(handle\w+|on\w+)\s*=\s*(?:async\s+)?function\s*\([^)]*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', re.DOTALL),
            # function handleClick() { ... }
            re.compile(r'(?:async\s+)?function\s+(handle\w+|on\w+)\s*\([^)]*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', re.DOTALL),
        ]

        for pattern in handler_patterns:
            for match in pattern.finditer(content):
                handler_name = match.group(1)
                handler_body = match.group(2) if len(match.groups()) > 1 else ""
                handlers[handler_name] = handler_body

        return handlers

    def _find_interactive_elements(self, content: str, file_path: str) -> List[UIElement]:
        """
        Find all interactive UI elements in a file.
        """
        elements: List[UIElement] = []

        # Find buttons with onClick
        button_pattern = re.compile(
            r'<(?:button|Button)[^>]*?(?:onClick\s*=\s*\{?\s*(\w+))?[^>]*>([^<]*)<',
            re.IGNORECASE | re.DOTALL
        )

        for match in button_pattern.finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            handler_name = match.group(1)
            text_content = match.group(2).strip() if match.group(2) else None

            element = UIElement(
                element_id=self._generate_element_id(),
                element_type=UIElementType.BUTTON,
                location={"file": file_path, "line": line_num},
                text_content=text_content,
                handler_name=handler_name,
            )
            elements.append(element)

        # Find elements with onClick but not buttons
        onclick_pattern = re.compile(
            r'<(\w+)[^>]*?onClick\s*=\s*\{?\s*(\w+)[^>]*>',
            re.IGNORECASE
        )

        for match in onclick_pattern.finditer(content):
            tag_name = match.group(1).lower()
            if tag_name not in {"button", "Button"}:
                line_num = content[:match.start()].count("\n") + 1
                handler_name = match.group(2)

                element_type = UIElementType.BUTTON  # Default for clickable
                if tag_name == "a":
                    element_type = UIElementType.LINK
                elif tag_name in {"li", "div", "span"}:
                    element_type = UIElementType.MENU_ITEM

                element = UIElement(
                    element_id=self._generate_element_id(),
                    element_type=element_type,
                    location={"file": file_path, "line": line_num},
                    handler_name=handler_name,
                )
                elements.append(element)

        return elements

    def _analyze_handler_effects(self, handler_body: str) -> Set[EffectType]:
        """
        Analyze a handler body to determine what effects it has.
        """
        if not handler_body or not handler_body.strip():
            return {EffectType.NONE}

        # Remove comments
        cleaned = re.sub(r'//.*$', '', handler_body, flags=re.MULTILINE)
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
        cleaned = cleaned.strip()

        if not cleaned or cleaned in {';', 'return;', 'return'}:
            return {EffectType.NONE}

        effects: Set[EffectType] = set()

        for effect_type, patterns in self.EFFECT_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(handler_body):
                    effects.add(effect_type)

        if not effects:
            # Check if there's any actual code
            code_pattern = re.compile(r'\w+\s*\(')  # Any function call
            if code_pattern.search(cleaned):
                effects.add(EffectType.CALLBACK)  # Assume some callback
            else:
                effects.add(EffectType.NONE)

        return effects


def verify_ui(path: Path) -> UIVerificationReport:
    """
    Convenience function to verify UI elements.
    """
    verifier = UIVerifier()
    if path.is_file():
        return verifier.verify_file(path)
    else:
        return verifier.verify_directory(path)
