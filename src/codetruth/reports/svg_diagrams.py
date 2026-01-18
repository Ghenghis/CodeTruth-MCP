"""
SVG Diagram Generator

Generates visual diagrams for audit reports including:
- Architecture diagrams
- Call graphs
- Dependency graphs
- UI flow diagrams
- Coverage maps
"""

from __future__ import annotations

from typing import Any
import html


class SVGDiagramGenerator:
    """Generates SVG diagrams for audit visualization."""

    # Color schemes
    COLORS = {
        "primary": "#3b82f6",
        "secondary": "#6366f1",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "neutral": "#6b7280",
        "background": "#f8fafc",
        "text": "#1e293b",
        "border": "#e2e8f0",
    }

    COMPONENT_COLORS = {
        "page": "#3b82f6",
        "component": "#6366f1",
        "hook": "#8b5cf6",
        "context": "#a855f7",
        "service": "#22c55e",
        "api": "#f59e0b",
        "database": "#06b6d4",
    }

    def generate_architecture_diagram(self, inventory: dict[str, Any]) -> str:
        """Generate codebase architecture diagram."""
        width = 800
        height = 600

        svg = self._svg_header(width, height, "Codebase Architecture")

        # Draw layers
        layers = [
            ("UI Layer", ["page", "component", "hook"]),
            ("API Layer", ["api", "route_handler"]),
            ("Service Layer", ["service", "middleware"]),
            ("Data Layer", ["database", "model"]),
        ]

        y_offset = 80
        layer_height = 120

        for i, (layer_name, types) in enumerate(layers):
            y = y_offset + i * layer_height

            # Layer background
            svg += f'''
    <rect x="50" y="{y}" width="700" height="{layer_height - 20}"
          fill="{self.COLORS['background']}" stroke="{self.COLORS['border']}"
          stroke-width="2" rx="10"/>
    <text x="70" y="{y + 25}" font-family="Arial" font-size="14"
          font-weight="bold" fill="{self.COLORS['text']}">{layer_name}</text>
'''

            # Draw components in layer
            components = self._get_components_for_layer(inventory, types)
            x_offset = 80
            for j, comp in enumerate(components[:8]):  # Max 8 per layer
                x = x_offset + j * 85
                color = self.COMPONENT_COLORS.get(comp.get("type", "component"), self.COLORS["neutral"])

                svg += f'''
    <rect x="{x}" y="{y + 40}" width="75" height="50"
          fill="{color}" rx="5" opacity="0.8"/>
    <text x="{x + 37}" y="{y + 70}" font-family="Arial" font-size="10"
          fill="white" text-anchor="middle">{html.escape(comp.get('name', 'Unknown')[:10])}</text>
'''

        svg += self._svg_footer()
        return svg

    def generate_call_graph(self, call_graph: dict[str, Any]) -> str:
        """Generate function call graph diagram."""
        width = 900
        height = 700

        svg = self._svg_header(width, height, "Call Graph")

        nodes = call_graph.get("nodes", [])
        edges = call_graph.get("edges", [])

        if not nodes:
            # Generate sample/placeholder
            svg += '''
    <text x="450" y="350" font-family="Arial" font-size="16"
          fill="{}" text-anchor="middle">No call graph data available</text>
'''.format(self.COLORS['neutral'])
        else:
            # Position nodes in a circle
            import math
            center_x, center_y = 450, 350
            radius = 250
            node_positions = {}

            for i, node in enumerate(nodes[:20]):  # Max 20 nodes
                angle = (2 * math.pi * i) / min(len(nodes), 20)
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                node_positions[node.get("id", str(i))] = (x, y)

                # Draw node
                node_type = node.get("type", "function")
                color = self.COMPONENT_COLORS.get(node_type, self.COLORS["primary"])

                svg += f'''
    <circle cx="{x}" cy="{y}" r="30" fill="{color}" opacity="0.8"/>
    <text x="{x}" y="{y + 5}" font-family="Arial" font-size="10"
          fill="white" text-anchor="middle">{html.escape(node.get('name', '?')[:8])}</text>
'''

            # Draw edges
            for edge in edges[:50]:  # Max 50 edges
                from_id = edge.get("from")
                to_id = edge.get("to")
                if from_id in node_positions and to_id in node_positions:
                    x1, y1 = node_positions[from_id]
                    x2, y2 = node_positions[to_id]

                    svg += f'''
    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
          stroke="{self.COLORS['neutral']}" stroke-width="1" opacity="0.5"
          marker-end="url(#arrowhead)"/>
'''

        # Add arrowhead marker
        svg += '''
    <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="7"
                refX="10" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="{}"/>
        </marker>
    </defs>
'''.format(self.COLORS['neutral'])

        svg += self._svg_footer()
        return svg

    def generate_dependency_graph(self, inventory: dict[str, Any]) -> str:
        """Generate package dependency graph."""
        width = 800
        height = 600

        svg = self._svg_header(width, height, "Dependency Graph")

        # Get integrations/dependencies
        integrations = inventory.get("external_integrations", [])
        manifests = inventory.get("manifests", {})

        if not integrations and not manifests:
            svg += f'''
    <text x="400" y="300" font-family="Arial" font-size="16"
          fill="{self.COLORS['neutral']}" text-anchor="middle">No dependency data available</text>
'''
        else:
            # Center node (the project)
            svg += f'''
    <circle cx="400" cy="300" r="50" fill="{self.COLORS['primary']}"/>
    <text x="400" y="305" font-family="Arial" font-size="12"
          fill="white" text-anchor="middle" font-weight="bold">Project</text>
'''

            # Draw dependencies around
            import math
            deps = integrations[:12]  # Max 12
            for i, dep in enumerate(deps):
                angle = (2 * math.pi * i) / max(len(deps), 1)
                x = 400 + 180 * math.cos(angle)
                y = 300 + 180 * math.sin(angle)

                svg += f'''
    <line x1="400" y1="300" x2="{x}" y2="{y}"
          stroke="{self.COLORS['border']}" stroke-width="2"/>
    <circle cx="{x}" cy="{y}" r="35" fill="{self.COLORS['secondary']}" opacity="0.8"/>
    <text x="{x}" y="{y + 5}" font-family="Arial" font-size="10"
          fill="white" text-anchor="middle">{html.escape(dep.get('name', '?')[:10])}</text>
'''

        svg += self._svg_footer()
        return svg

    def generate_ui_flow(
        self,
        components: list[dict[str, Any]],
        routes: list[dict[str, Any]],
    ) -> str:
        """Generate UI component flow diagram."""
        width = 900
        height = 700

        svg = self._svg_header(width, height, "UI Component Flow")

        # Draw routes as entry points on the left
        y_offset = 100
        route_positions = {}

        for i, route in enumerate(routes[:10]):
            y = y_offset + i * 55
            route_positions[route.get("path", f"route_{i}")] = (100, y)

            svg += f'''
    <rect x="30" y="{y - 15}" width="140" height="30"
          fill="{self.COLORS['success']}" rx="5"/>
    <text x="100" y="{y + 3}" font-family="Arial" font-size="11"
          fill="white" text-anchor="middle">{html.escape(route.get('path', '/')[:15])}</text>
'''

        # Draw components in the middle/right
        component_positions = {}
        pages = [c for c in components if c.get("component_type") == "page"]
        other_components = [c for c in components if c.get("component_type") != "page"][:15]

        # Pages
        for i, page in enumerate(pages[:8]):
            x = 250
            y = 80 + i * 70
            component_positions[page.get("name", f"page_{i}")] = (x, y)

            svg += f'''
    <rect x="{x - 50}" y="{y - 20}" width="100" height="40"
          fill="{self.COMPONENT_COLORS['page']}" rx="5"/>
    <text x="{x}" y="{y + 5}" font-family="Arial" font-size="10"
          fill="white" text-anchor="middle">{html.escape(page.get('name', 'Page')[:12])}</text>
'''

        # Other components
        for i, comp in enumerate(other_components):
            x = 450 + (i % 3) * 130
            y = 80 + (i // 3) * 60
            comp_type = comp.get("component_type", "component")
            color = self.COMPONENT_COLORS.get(comp_type, self.COLORS['secondary'])

            svg += f'''
    <rect x="{x - 45}" y="{y - 18}" width="90" height="36"
          fill="{color}" rx="5" opacity="0.9"/>
    <text x="{x}" y="{y + 5}" font-family="Arial" font-size="9"
          fill="white" text-anchor="middle">{html.escape(comp.get('name', 'Comp')[:10])}</text>
'''

        # Draw connections from routes to pages
        for route in routes[:10]:
            route_path = route.get("path", "")
            component_name = route.get("component", "")
            if route_path in route_positions and component_name:
                x1, y1 = route_positions[route_path]
                # Find matching component
                for name, (x2, y2) in component_positions.items():
                    if name.lower() in component_name.lower() or component_name.lower() in name.lower():
                        svg += f'''
    <line x1="{x1 + 70}" y1="{y1}" x2="{x2 - 50}" y2="{y2}"
          stroke="{self.COLORS['neutral']}" stroke-width="1.5"
          stroke-dasharray="5,3" opacity="0.6"/>
'''
                        break

        # Legend
        svg += f'''
    <rect x="30" y="{height - 80}" width="200" height="60"
          fill="white" stroke="{self.COLORS['border']}" rx="5"/>
    <text x="40" y="{height - 60}" font-family="Arial" font-size="10"
          font-weight="bold" fill="{self.COLORS['text']}">Legend</text>
    <rect x="40" y="{height - 50}" width="15" height="10" fill="{self.COLORS['success']}"/>
    <text x="60" y="{height - 42}" font-family="Arial" font-size="9">Route</text>
    <rect x="100" y="{height - 50}" width="15" height="10" fill="{self.COMPONENT_COLORS['page']}"/>
    <text x="120" y="{height - 42}" font-family="Arial" font-size="9">Page</text>
    <rect x="160" y="{height - 50}" width="15" height="10" fill="{self.COMPONENT_COLORS['component']}"/>
    <text x="180" y="{height - 42}" font-family="Arial" font-size="9">Component</text>
'''

        svg += self._svg_footer()
        return svg

    def generate_coverage_map(self, coverage: dict[str, Any]) -> str:
        """Generate test coverage visualization."""
        width = 800
        height = 500

        svg = self._svg_header(width, height, "Test Coverage Map")

        files = coverage.get("files", {})

        if not files:
            # Generate placeholder with example
            svg += f'''
    <text x="400" y="250" font-family="Arial" font-size="16"
          fill="{self.COLORS['neutral']}" text-anchor="middle">Coverage data will appear after running tests</text>
'''
        else:
            # Create a treemap-style visualization
            x_offset = 50
            y_offset = 80
            cell_width = 100
            cell_height = 60

            for i, (file_path, file_coverage) in enumerate(list(files.items())[:30]):
                row = i // 7
                col = i % 7
                x = x_offset + col * cell_width
                y = y_offset + row * cell_height

                pct = file_coverage.get("line_coverage", 0)
                color = self._coverage_color(pct)

                # Truncate filename
                filename = file_path.split("/")[-1][:12]

                svg += f'''
    <rect x="{x}" y="{y}" width="{cell_width - 5}" height="{cell_height - 5}"
          fill="{color}" rx="3" stroke="{self.COLORS['border']}"/>
    <text x="{x + cell_width/2 - 2}" y="{y + 25}" font-family="Arial" font-size="9"
          fill="white" text-anchor="middle">{html.escape(filename)}</text>
    <text x="{x + cell_width/2 - 2}" y="{y + 40}" font-family="Arial" font-size="11"
          fill="white" text-anchor="middle" font-weight="bold">{pct:.0f}%</text>
'''

        # Coverage legend
        svg += f'''
    <rect x="50" y="{height - 60}" width="300" height="40"
          fill="white" stroke="{self.COLORS['border']}" rx="5"/>
    <text x="60" y="{height - 42}" font-family="Arial" font-size="10" font-weight="bold">Coverage:</text>
'''
        legend_items = [
            ("0-25%", self._coverage_color(12.5)),
            ("25-50%", self._coverage_color(37.5)),
            ("50-75%", self._coverage_color(62.5)),
            ("75-100%", self._coverage_color(87.5)),
        ]
        for i, (label, color) in enumerate(legend_items):
            x = 130 + i * 60
            svg += f'''
    <rect x="{x}" y="{height - 48}" width="15" height="15" fill="{color}" rx="2"/>
    <text x="{x + 18}" y="{height - 37}" font-family="Arial" font-size="9">{label}</text>
'''

        svg += self._svg_footer()
        return svg

    def _coverage_color(self, percentage: float) -> str:
        """Get color based on coverage percentage."""
        if percentage >= 80:
            return self.COLORS["success"]
        elif percentage >= 60:
            return "#84cc16"  # lime
        elif percentage >= 40:
            return self.COLORS["warning"]
        elif percentage >= 20:
            return "#f97316"  # orange
        else:
            return self.COLORS["error"]

    def _get_components_for_layer(
        self,
        inventory: dict[str, Any],
        types: list[str],
    ) -> list[dict[str, Any]]:
        """Get components that belong to a layer."""
        components = []

        # From UI components
        for comp in inventory.get("ui_components", []):
            comp_type = comp.get("component_type", "")
            if comp_type in types:
                components.append({"name": comp.get("name"), "type": comp_type})

        # From API routes
        if "api" in types or "route_handler" in types:
            for route in inventory.get("api_routes", []):
                components.append({
                    "name": f"{route.get('method', 'GET')} {route.get('path', '/')[:10]}",
                    "type": "api",
                })

        # From DB schemas
        if "database" in types or "model" in types:
            for schema in inventory.get("db_schemas", []):
                components.append({
                    "name": schema.get("name"),
                    "type": "database",
                })

        return components

    def _svg_header(self, width: int, height: int, title: str) -> str:
        """Generate SVG header."""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
     xmlns="http://www.w3.org/2000/svg">
    <rect width="100%" height="100%" fill="white"/>
    <text x="{width // 2}" y="40" font-family="Arial" font-size="20"
          font-weight="bold" fill="{self.COLORS['text']}" text-anchor="middle">{title}</text>
'''

    def _svg_footer(self) -> str:
        """Generate SVG footer."""
        return "\n</svg>"
