"""
HTML page generator using Jinja2 templates.
"""

import os
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, Template
import pandas as pd
from datetime import datetime

from .config import Config


class PageGenerator:
    """Generate HTML pages for neuron types."""
    
    def __init__(self, config: Config, output_dir: str):
        """Initialize the page generator."""
        self.config = config
        self.output_dir = Path(output_dir)
        self.template_dir = Path(config.output.template_dir)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self._setup_jinja_env()
    
    def _setup_jinja_env(self):
        """Set up Jinja2 environment with templates."""
        # Create template directory if it doesn't exist
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default template if none exists
        default_template = self.template_dir / "neuron_page.html"
        if not default_template.exists():
            self._create_default_template()
        
        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # Add custom filters
        self.env.filters['format_number'] = self._format_number
        self.env.filters['format_percentage'] = self._format_percentage
    
    def _create_default_template(self):
        """Create a default HTML template."""
        template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ config.html.title_prefix }} - {{ neuron_data.type }}</title>
    <link rel="stylesheet" href="https://unpkg.com/@pulsecss/pulse@latest/dist/pulse.min.css">
    <style>
        .neuron-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }
        .data-table {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .sidebar {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 8px;
        }
    </style>
</head>
<body class="bg-gray-50">
    <div class="neuron-header">
        <div class="container mx-auto">
            <h1 class="text-4xl font-bold mb-2">{{ neuron_data.type }}</h1>
            <p class="text-xl opacity-90">{{ soma_side|title }} hemisphere analysis</p>
            <p class="opacity-75">Generated on {{ generation_time.strftime('%Y-%m-%d %H:%M') }}</p>
        </div>
    </div>

    <div class="container mx-auto px-4">
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <!-- Main content -->
            <div class="lg:col-span-3">
                <!-- Summary statistics -->
                <section class="mb-8">
                    <h2 class="text-2xl font-bold mb-4">Summary Statistics</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div class="stat-card text-center">
                            <div class="stat-number">{{ summary.total_count }}</div>
                            <div class="text-gray-600">Total Neurons</div>
                        </div>
                        <div class="stat-card text-center">
                            <div class="stat-number">{{ summary.left_count }}</div>
                            <div class="text-gray-600">Left Side</div>
                        </div>
                        <div class="stat-card text-center">
                            <div class="stat-number">{{ summary.right_count }}</div>
                            <div class="text-gray-600">Right Side</div>
                        </div>
                        <div class="stat-card text-center">
                            <div class="stat-number">{{ summary.total_pre_synapses|format_number }}</div>
                            <div class="text-gray-600">Pre-synapses</div>
                        </div>
                    </div>
                </section>

                <!-- Neuron details -->
                {% if neurons_df is not none and not neurons_df.empty %}
                <section class="mb-8">
                    <h2 class="text-2xl font-bold mb-4">Neuron Details</h2>
                    <div class="data-table">
                        <div class="overflow-x-auto">
                            <table class="w-full">
                                <thead class="bg-gray-100">
                                    <tr>
                                        <th class="px-4 py-3 text-left">Body ID</th>
                                        <th class="px-4 py-3 text-left">Instance</th>
                                        <th class="px-4 py-3 text-center">Pre</th>
                                        <th class="px-4 py-3 text-center">Post</th>
                                        {% if 'somaLocation' in neurons_df.columns %}
                                        <th class="px-4 py-3 text-center">Soma Side</th>
                                        {% endif %}
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for _, neuron in neurons_df.iterrows() %}
                                    <tr class="border-t hover:bg-gray-50">
                                        <td class="px-4 py-3 font-mono">{{ neuron.name }}</td>
                                        <td class="px-4 py-3">{{ neuron.get('instance', 'N/A') }}</td>
                                        <td class="px-4 py-3 text-center">{{ neuron.get('pre', 0) }}</td>
                                        <td class="px-4 py-3 text-center">{{ neuron.get('post', 0) }}</td>
                                        {% if 'somaLocation' in neurons_df.columns %}
                                        <td class="px-4 py-3 text-center">{{ neuron.get('somaLocation', 'N/A') }}</td>
                                        {% endif %}
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </section>
                {% endif %}
            </div>

            <!-- Sidebar -->
            <div class="lg:col-span-1">
                <div class="sidebar">
                    <h3 class="text-lg font-bold mb-4">Analysis Details</h3>
                    <div class="space-y-3">
                        <div>
                            <span class="font-medium">Dataset:</span><br>
                            <span class="text-gray-600">{{ config.neuprint.dataset }}</span>
                        </div>
                        <div>
                            <span class="font-medium">Server:</span><br>
                            <span class="text-gray-600">{{ config.neuprint.server }}</span>
                        </div>
                        <div>
                            <span class="font-medium">Soma Side:</span><br>
                            <span class="text-gray-600">{{ soma_side|title }}</span>
                        </div>
                        {% if summary.avg_pre_synapses > 0 %}
                        <div>
                            <span class="font-medium">Avg Pre-synapses:</span><br>
                            <span class="text-gray-600">{{ summary.avg_pre_synapses }}</span>
                        </div>
                        {% endif %}
                        {% if summary.avg_post_synapses > 0 %}
                        <div>
                            <span class="font-medium">Avg Post-synapses:</span><br>
                            <span class="text-gray-600">{{ summary.avg_post_synapses }}</span>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="mt-12 py-8 bg-gray-800 text-white text-center">
        <p>Generated by QuickPage • Data from {{ config.neuprint.server }}</p>
    </footer>
</body>
</html>'''
        
        template_file = self.template_dir / "neuron_page.html"
        with open(template_file, 'w') as f:
            f.write(template_content)
    
    def generate_page(self, neuron_type: str, neuron_data: Dict[str, Any], 
                     soma_side: str) -> str:
        """
        Generate an HTML page for a neuron type.
        
        Args:
            neuron_type: The neuron type name
            neuron_data: Data returned from NeuPrintConnector
            soma_side: Soma side filter used
            
        Returns:
            Path to the generated HTML file
        """
        # Load template
        template = self.env.get_template('neuron_page.html')
        
        # Prepare template context
        context = {
            'config': self.config,
            'neuron_data': neuron_data,
            'neuron_type': neuron_type,
            'soma_side': soma_side,
            'summary': neuron_data['summary'],
            'neurons_df': neuron_data['neurons'],
            'connectivity': neuron_data.get('connectivity', {}),
            'generation_time': datetime.now()
        }
        
        # Render template
        html_content = template.render(**context)
        
        # Generate output filename
        output_filename = self._generate_filename(neuron_type, soma_side)
        output_path = self.output_dir / output_filename
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_path)
    
    def _generate_filename(self, neuron_type: str, soma_side: str) -> str:
        """Generate output filename based on neuron type and soma side."""
        # Clean neuron type name for filename
        clean_type = neuron_type.replace('/', '_').replace(' ', '_')
        
        if soma_side == 'both':
            return f"{clean_type}_neuron_report.html"
        else:
            return f"{clean_type}_{soma_side}_neuron_report.html"
    
    def _format_number(self, value: Any) -> str:
        """Format numbers with commas."""
        if isinstance(value, (int, float)):
            return f"{value:,}"
        return str(value)
    
    def _format_percentage(self, value: Any) -> str:
        """Format numbers as percentages."""
        if isinstance(value, (int, float)):
            return f"{value:.1f}%"
        return str(value)
