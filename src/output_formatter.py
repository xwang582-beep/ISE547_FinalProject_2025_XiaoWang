"""
Output Formatter Module
Formats FAQ data into various output formats
"""

import json
from typing import List, Dict
from pathlib import Path
from datetime import datetime


class OutputFormatter:
    """Format FAQs into different output formats"""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize Output Formatter
        
        Args:
            output_dir: Directory to save outputs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def to_markdown(
        self,
        faqs: List[Dict],
        output_path: str,
        title: str = "Frequently Asked Questions",
        source_file: str = ""
    ) -> str:
        """
        Export FAQs to Markdown format
        
        Args:
            faqs: List of FAQ dictionaries
            output_path: Path to save markdown file
            title: Title for the FAQ document
            source_file: Name of source document
            
        Returns:
            Path to created file
        """
        output_path = self.output_dir / output_path
        
        md_content = f"# {title}\n\n"
        
        if source_file:
            md_content += f"**Source Document:** {source_file}\n\n"
        
        md_content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md_content += f"**Total Questions:** {len(faqs)}\n\n"
        md_content += "---\n\n"
        
        for i, faq in enumerate(faqs, 1):
            md_content += f"## {i}. {faq['question']}\n\n"
            md_content += f"{faq['answer']}\n\n"
            md_content += "---\n\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return str(output_path)
    
    def to_html(
        self,
        faqs: List[Dict],
        output_path: str,
        title: str = "Frequently Asked Questions",
        source_file: str = ""
    ) -> str:
        """
        Export FAQs to HTML format with search functionality
        
        Args:
            faqs: List of FAQ dictionaries
            output_path: Path to save HTML file
            title: Title for the FAQ document
            source_file: Name of source document
            
        Returns:
            Path to created file
        """
        output_path = self.output_dir / output_path
        
        # Generate FAQ items HTML
        faq_items = ""
        for i, faq in enumerate(faqs, 1):
            faq_items += f"""
            <div class="faq-item" data-index="{i}">
                <div class="question" onclick="toggleAnswer(this)">
                    <span class="number">{i}.</span>
                    <span class="question-text">{self._escape_html(faq['question'])}</span>
                    <span class="toggle">▼</span>
                </div>
                <div class="answer">
                    <p>{self._escape_html(faq['answer'])}</p>
                </div>
            </div>
            """
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header .meta {{
            opacity: 0.9;
            font-size: 0.95em;
        }}
        
        .search-box {{
            padding: 20px 40px;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .search-input {{
            width: 100%;
            padding: 12px 20px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 25px;
            outline: none;
            transition: border-color 0.3s;
        }}
        
        .search-input:focus {{
            border-color: #667eea;
        }}
        
        .stats {{
            padding: 15px 40px;
            background: #f0f0f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.9em;
            color: #666;
        }}
        
        .faq-list {{
            padding: 20px 40px 40px;
        }}
        
        .faq-item {{
            margin-bottom: 15px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
            transition: box-shadow 0.3s;
        }}
        
        .faq-item:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .question {{
            padding: 20px;
            background: #f8f9fa;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            user-select: none;
        }}
        
        .question:hover {{
            background: #e9ecef;
        }}
        
        .number {{
            font-weight: bold;
            color: #667eea;
            min-width: 30px;
        }}
        
        .question-text {{
            flex: 1;
            font-weight: 600;
            color: #333;
        }}
        
        .toggle {{
            color: #667eea;
            transition: transform 0.3s;
        }}
        
        .question.active .toggle {{
            transform: rotate(180deg);
        }}
        
        .answer {{
            padding: 0 20px;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out, padding 0.3s;
            background: white;
        }}
        
        .answer.show {{
            max-height: 1000px;
            padding: 20px;
        }}
        
        .answer p {{
            color: #555;
            line-height: 1.8;
        }}
        
        .hidden {{
            display: none !important;
        }}
        
        .no-results {{
            text-align: center;
            padding: 40px;
            color: #999;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="meta">
                {f'<p>Source: {source_file}</p>' if source_file else ''}
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
        
        <div class="search-box">
            <input 
                type="text" 
                class="search-input" 
                placeholder="🔍 Search questions and answers..."
                onkeyup="searchFAQs(this.value)"
            >
        </div>
        
        <div class="stats">
            <span>Total Questions: <strong id="total-count">{len(faqs)}</strong></span>
            <span>Showing: <strong id="visible-count">{len(faqs)}</strong></span>
        </div>
        
        <div class="faq-list" id="faq-list">
            {faq_items}
        </div>
        
        <div class="no-results hidden" id="no-results">
            <p>No matching questions found. Try a different search term.</p>
        </div>
        
        <div class="footer">
            <p>Generated by Smart FAQ Generator</p>
        </div>
    </div>
    
    <script>
        function toggleAnswer(element) {{
            const answer = element.nextElementSibling;
            const isOpen = answer.classList.contains('show');
            
            // Close all answers
            document.querySelectorAll('.answer').forEach(a => a.classList.remove('show'));
            document.querySelectorAll('.question').forEach(q => q.classList.remove('active'));
            
            // Toggle current answer
            if (!isOpen) {{
                answer.classList.add('show');
                element.classList.add('active');
            }}
        }}
        
        function searchFAQs(query) {{
            const items = document.querySelectorAll('.faq-item');
            const noResults = document.getElementById('no-results');
            let visibleCount = 0;
            
            query = query.toLowerCase().trim();
            
            items.forEach(item => {{
                const question = item.querySelector('.question-text').textContent.toLowerCase();
                const answer = item.querySelector('.answer p').textContent.toLowerCase();
                
                if (query === '' || question.includes(query) || answer.includes(query)) {{
                    item.classList.remove('hidden');
                    visibleCount++;
                }} else {{
                    item.classList.add('hidden');
                }}
            }});
            
            document.getElementById('visible-count').textContent = visibleCount;
            
            if (visibleCount === 0) {{
                noResults.classList.remove('hidden');
            }} else {{
                noResults.classList.add('hidden');
            }}
        }}
    </script>
</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        return str(output_path)
    
    def to_json(
        self,
        faqs: List[Dict],
        output_path: str,
        metadata: Dict = None
    ) -> str:
        """
        Export FAQs to JSON format
        
        Args:
            faqs: List of FAQ dictionaries
            output_path: Path to save JSON file
            metadata: Additional metadata to include
            
        Returns:
            Path to created file
        """
        output_path = self.output_dir / output_path
        
        output_data = {
            'metadata': metadata or {},
            'generated_at': datetime.now().isoformat(),
            'total_faqs': len(faqs),
            'faqs': faqs
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def to_txt(
        self,
        faqs: List[Dict],
        output_path: str,
        title: str = "Frequently Asked Questions"
    ) -> str:
        """
        Export FAQs to plain text format
        
        Args:
            faqs: List of FAQ dictionaries
            output_path: Path to save text file
            title: Title for the FAQ document
            
        Returns:
            Path to created file
        """
        output_path = self.output_dir / output_path
        
        content = f"{title}\n"
        content += "=" * len(title) + "\n\n"
        content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"Total Questions: {len(faqs)}\n\n"
        content += "-" * 80 + "\n\n"
        
        for i, faq in enumerate(faqs, 1):
            content += f"Q{i}: {faq['question']}\n\n"
            content += f"A{i}: {faq['answer']}\n\n"
            content += "-" * 80 + "\n\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(output_path)
    
    def _escape_html(self, text: str) -> str:
        """
        Escape HTML special characters
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text
        """
        return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


# Example usage
if __name__ == "__main__":
    # Test with sample FAQs
    sample_faqs = [
        {
            'question': 'What is this project about?',
            'answer': 'This project generates FAQs from documents automatically.'
        },
        {
            'question': 'How does it work?',
            'answer': 'It uses LLMs to analyze text and create relevant question-answer pairs.'
        }
    ]
    
    formatter = OutputFormatter()
    
    print("Testing output formats...")
    md_path = formatter.to_markdown(sample_faqs, "test.md")
    print(f"Markdown saved to: {md_path}")
    
    html_path = formatter.to_html(sample_faqs, "test.html")
    print(f"HTML saved to: {html_path}")
    
    json_path = formatter.to_json(sample_faqs, "test.json")
    print(f"JSON saved to: {json_path}")

