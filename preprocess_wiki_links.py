#!/usr/bin/env python3
"""
Preprocess Obsidian wiki links to Markdown links for MkDocs.
Converts [[Link Text]] to [Link Text](../path/to/Link%20Text.md)
Handles subdirectories and special characters.
"""

import os
import re
from pathlib import Path

# Build a map of wiki link names to file paths
def build_link_map(docs_dir):
    """Scan docs directory and create a map of page names to relative paths."""
    link_map = {}
    
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                filepath = Path(root) / file
                # Get the page name (filename without .md)
                page_name = file[:-3]
                # Store the relative path from docs_dir
                rel_path = filepath.relative_to(docs_dir)
                link_map[page_name] = str(rel_path)
    
    return link_map

def get_relative_path(from_file, to_file):
    """
    Calculate relative path from one file to another.
    Both should be relative to docs_dir.
    """
    from_parts = Path(from_file).parts[:-1]  # Remove filename, keep directory parts
    to_parts = Path(to_file).parts
    
    # Find common prefix
    common = 0
    for i, (f, t) in enumerate(zip(from_parts, to_parts)):
        if f == t:
            common = i + 1
        else:
            break
    
    # Build relative path
    ups = ['..'] * (len(from_parts) - common)
    downs = list(to_parts[common:])
    rel_parts = ups + downs
    
    return '/'.join(rel_parts)


def convert_wiki_links_in_file(filepath, link_map, docs_dir):
    """Convert [[Link]] syntax to [Link](path) in a markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    file_rel = str(filepath.relative_to(docs_dir)).replace('\\', '/')
    
    # Pattern: [[Text]] or [[Text|Display Text]]
    def replace_link(match):
        link_text = match.group(1)
        
        # Handle [[Text|Display]] format
        if '|' in link_text:
            target, display = link_text.split('|', 1)
            target = target.strip()
            display = display.strip()
        else:
            target = link_text.strip()
            display = target
        
        # Look up the file in link_map
        if target in link_map:
            target_path = link_map[target].replace('\\', '/')
            rel_path = get_relative_path(file_rel, target_path)
            # URL-encode spaces
            rel_path = rel_path.replace(' ', '%20')
            return f'[{display}]({rel_path})'
        else:
            # Keep original if not found
            return match.group(0)
    
    # Replace all wiki links
    content = re.sub(r'\[\[([^\]]+)\]\]', replace_link, content)
    
    # Write back if changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    docs_dir = Path('docs/Worldbuilding')
    if not docs_dir.exists():
        print(f"Error: {docs_dir} does not exist")
        return
    
    print(f"Building link map from {docs_dir}...")
    link_map = build_link_map(docs_dir)
    print(f"Found {len(link_map)} pages")
    
    # Convert wiki links in all markdown files
    converted = 0
    for filepath in docs_dir.rglob('*.md'):
        if convert_wiki_links_in_file(filepath, link_map, docs_dir):
            converted += 1
            print(f"  ✓ {filepath.relative_to(docs_dir)}")
    
    print(f"\nConverted {converted} files")

if __name__ == '__main__':
    main()
