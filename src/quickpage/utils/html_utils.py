"""
HTML utilities module containing utility functions for HTML processing and generation.

This module extracts HTML-related functionality from the PageGenerator class
to improve code organization and reusability.
"""

from typing import Any


class HTMLUtils:
    """Utility class for HTML-related operations."""

    @staticmethod
    def is_png_data(content: str) -> bool:
        """Check if content is a PNG data URL."""
        if isinstance(content, str):
            return content.startswith('data:image/png;base64,')
        return False

    @staticmethod
    def create_neuron_link(neuron_type: str, soma_side: str, queue_service=None) -> str:
        """Create HTML link to neuron type page based on type and soma side."""
        # Check if we should create a link (only if neuron type is in queue)
        if queue_service:
            cached_types = queue_service.get_cached_neuron_types()
            if neuron_type not in cached_types:
                # Return just the display text without a link
                soma_side_lbl = ""
                if soma_side:
                    soma_side_lbl = f" ({soma_side})"
                return f"{neuron_type}{soma_side_lbl}"

        # Clean neuron type name for filename
        clean_type = neuron_type.replace('/', '_').replace(' ', '_')

        # Handle different soma side formats with new naming scheme
        if soma_side in ['all', 'combined', '']:
            # General page for neuron type (multiple sides available)
            filename = f"{clean_type}.html"
        else:
            # Specific page for single side
            soma_side_suffix = soma_side
            if soma_side_suffix == 'left':
                soma_side_suffix = 'L'
            elif soma_side_suffix == 'right':
                soma_side_suffix = 'R'
            elif soma_side_suffix == 'middle':
                soma_side_suffix = 'M'
            filename = f"{clean_type}_{soma_side_suffix}.html#s-c"

        # Create the display text (same as original)
        soma_side_lbl = ""
        if soma_side:
            soma_side_lbl = f" ({soma_side})"
        display_text = f"{neuron_type}{soma_side_lbl}"

        # Return HTML link
        return f'<a href="{filename}">{display_text}</a>'

    @staticmethod
    def minify_html(html_content: str, minify_js: bool = True) -> str:
        """
        Minify HTML content by removing unnecessary whitespace.

        Args:
            html_content: Raw HTML content to minify
            minify_js: Whether to minify JavaScript content within script tags

        Returns:
            Minified HTML content
        """
        import minify_html
        import re
        import logging

        logger = logging.getLogger(__name__)

        # Check for problematic JavaScript patterns that cause minify-js to panic
        # The minify-js 0.6.0 library has severe bugs with control flow statements
        # Testing shows it fails on: if statements, switch, loops, try-catch, functions
        # Safe patterns: variable declarations, ternary operators, simple function calls
        has_problematic_js = False

        if minify_js:
            # Look for problematic patterns inside script tags
            script_pattern = r'<script[^>]*>(.*?)</script>'
            scripts = re.findall(script_pattern, html_content, re.DOTALL | re.IGNORECASE)

            for i, script_content in enumerate(scripts):
                # Skip external scripts (just src attribute, no inline content)
                if script_content.strip() == '':
                    continue

                # Skip scripts that only contain safe patterns
                # Safe patterns: simple variable declarations, function calls, ternary operators
                safe_only_pattern = r'^[\s\n]*(?:(?:var|let|const)\s+\w+\s*=\s*[^;]+;|[\w.$]+\([^)]*\);|\w+\s*=\s*[^?]*\?[^:]*:[^;]+;|//[^\n]*|/\*.*?\*/|\s)*[\s\n]*$'

                if re.match(safe_only_pattern, script_content, re.DOTALL):
                    logger.debug(f"Script {i}: Contains only safe patterns, allowing minification")
                    continue

                # Check for problematic control flow patterns that cause minify-js to crash
                # These patterns were verified through testing to cause library panics
                problematic_patterns = [
                    (r'if\s*\([^)]+\)\s*\{', "if statement"),
                    (r'switch\s*\([^)]+\)\s*\{', "switch statement"),
                    (r'while\s*\([^)]+\)\s*\{', "while loop"),
                    (r'for\s*\([^)]*\)\s*\{', "for loop"),
                    (r'try\s*\{', "try-catch block"),
                    (r'function\s*\([^)]*\)\s*\{', "function declaration"),
                    (r'=>\s*\{', "arrow function with block"),
                ]

                for pattern, description in problematic_patterns:
                    if re.search(pattern, script_content, re.DOTALL):
                        logger.debug(f"Script {i}: Found {description} - minify-js 0.6.0 cannot handle these reliably")
                        has_problematic_js = True
                        break

                if has_problematic_js:
                    break

        # Use JS minification only if no problematic patterns are detected
        safe_minify_js = minify_js and not has_problematic_js

        if minify_js and has_problematic_js:
            logger.info("Skipping JavaScript minification due to known minify-js 0.6.0 library bugs with control flow statements")

        minified = minify_html.minify(html_content, minify_js=safe_minify_js, minify_css=True, remove_processing_instructions=True)
        return minified
