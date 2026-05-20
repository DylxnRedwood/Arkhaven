#!/usr/bin/env python3
"""
Restructure content for DM-only folder.

1. Replicate folder structure from docs/Worldbuilding to docs/Worldbuilding/_Private (excluding _Private)
2. For each markdown file, extract DM-specific sections to _Private version
3. Remove DM-specific sections from original files in Worldbuilding
"""

import os
import re
import shutil
from pathlib import Path

DOCS_DIR = Path("docs")
WORLDBUILDING_DIR = DOCS_DIR / "Worldbuilding"
PRIVATE_DIR = WORLDBUILDING_DIR / "_Private"

# DM-specific section headers to identify and extract
# These are ACTUAL section headers that appear in markdown files
DM_SECTIONS = [
    "Using the .* in Play",  # Regex pattern: "Using the Godscar in Play", etc.
    "Use in a Campaign",
    "Common Adventure Hooks",
    "Tone",  # Can be "Tone", "Tone and Themes", etc.
    "Possible Player Character Role",
]

# Content marked with these tags should be extracted as DM content
DM_TAGS = [
    "dm-lore",
    "false_saints",
]

def get_section_index(content, section_name):
    """
    Find the line index where a section starts.
    Returns (start_index, section_header_line) or None if not found.
    """
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Match heading levels 1-6: "## Section" or "### Section"
        if re.match(rf'^#+\s+{section_name}\s*$', line, re.IGNORECASE):
            return i, line
    return None


def extract_section(content, section_name):
    """
    Extract a section from content. Returns the section content including header.
    Includes everything from the section header until the next header of equal or higher level.
    """
    lines = content.split('\n')
    
    result = get_section_index(content, section_name)
    if result is None:
        return None
    
    start_idx, header_line = result
    header_level = len(header_line) - len(header_line.lstrip('#'))
    
    # Find the next header of equal or higher level (lower number = higher level)
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if line.startswith('#') and line.strip() != '':
            line_level = len(line) - len(line.lstrip('#'))
            if line_level <= header_level:
                end_idx = i
                break
    
    section_content = '\n'.join(lines[start_idx:end_idx]).rstrip()
    return section_content


def remove_section(content, section_name):
    """
    Remove a section from content.
    """
    lines = content.split('\n')
    
    result = get_section_index(content, section_name)
    if result is None:
        return content
    
    start_idx, header_line = result
    header_level = len(header_line) - len(header_line.lstrip('#'))
    
    # Find the next header of equal or higher level
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if line.startswith('#') and line.strip() != '':
            line_level = len(line) - len(line.lstrip('#'))
            if line_level <= header_level:
                end_idx = i
                break
    
    # Reconstruct content without this section
    before = '\n'.join(lines[:start_idx])
    after = '\n'.join(lines[end_idx:])
    
    # Clean up extra blank lines
    if before.strip() and after.strip():
        result = before.rstrip() + '\n\n' + after.lstrip()
    elif after.strip():
        result = after.lstrip()
    else:
        result = before.rstrip()
    
    return result.rstrip() + '\n' if result.strip() else ''


def extract_dm_content(filepath):
    """
    Extract all DM-specific sections from a markdown file.
    Returns the extracted content or None if no DM sections found.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if file has YAML frontmatter
    frontmatter = ""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[0] + '---' + parts[1] + '---\n'
            content = parts[2].lstrip('\n')
    
    extracted_sections = []
    
    # Try each DM section pattern
    for section_pattern in DM_SECTIONS:
        section = extract_section(content, section_pattern)
        if section:
            extracted_sections.append(section)
    
    if not extracted_sections:
        return None
    
    # Combine all extracted sections
    dm_content = frontmatter + '\n\n'.join(extracted_sections)
    return dm_content


def remove_dm_content(filepath):
    """
    Remove all DM-specific sections from a markdown file.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Separate frontmatter
    frontmatter = ""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[0] + '---' + parts[1] + '---\n'
            content = parts[2].lstrip('\n')
    
    # Remove each DM section
    for section_pattern in DM_SECTIONS:
        content = remove_section(content, section_pattern)
    
    result = frontmatter + content
    
    # Clean up excess blank lines
    result = re.sub(r'\n\n\n+', '\n\n', result)
    
    return result.rstrip() + '\n'


def replicate_structure():
    """Create folder structure in _Private mirroring Worldbuilding (excluding _Private itself)."""
    for root, dirs, files in os.walk(WORLDBUILDING_DIR):
        # Skip _Private folder
        dirs[:] = [d for d in dirs if d != '_Private']
        
        rel_path = Path(root).relative_to(WORLDBUILDING_DIR)
        target_dir = PRIVATE_DIR / rel_path
        target_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✓ Created directory: {target_dir.relative_to(DOCS_DIR)}")


def process_files():
    """Process all markdown files."""
    files_with_dm_content = 0
    files_processed = 0
    
    for root, dirs, files in os.walk(WORLDBUILDING_DIR):
        # Skip _Private folder
        dirs[:] = [d for d in dirs if d != '_Private']
        
        for file in files:
            if file.endswith('.md'):
                original_path = Path(root) / file
                rel_path = original_path.relative_to(WORLDBUILDING_DIR)
                private_path = PRIVATE_DIR / rel_path
                
                # Extract DM content
                dm_content = extract_dm_content(original_path)
                
                if dm_content:
                    # Write DM-only version to _Private
                    with open(private_path, 'w', encoding='utf-8') as f:
                        f.write(dm_content)
                    print(f"✓ Created DM-only version: {private_path.relative_to(DOCS_DIR)}")
                    files_with_dm_content += 1
                    
                    # Remove DM sections from original
                    clean_content = remove_dm_content(original_path)
                    with open(original_path, 'w', encoding='utf-8') as f:
                        f.write(clean_content)
                    print(f"  Removed DM content from: {original_path.relative_to(DOCS_DIR)}")
                
                files_processed += 1
    
    return files_processed, files_with_dm_content


def main():
    print("Restructuring content for DM-only folder...\n")
    
    # Step 1: Create folder structure
    print("Step 1: Replicating folder structure...")
    replicate_structure()
    
    # Step 2: Process files
    print("\nStep 2: Processing markdown files...")
    total, with_dm = process_files()
    
    print(f"\n✓ Complete!")
    print(f"  - Processed {total} markdown files")
    print(f"  - Created {with_dm} DM-only versions in _Private/")
    print(f"  - Removed DM content from all original files")


if __name__ == "__main__":
    main()
