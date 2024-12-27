def parse_article_content(content: str):
    """Parse article content with metadata"""
    lines = content.split('\n')
    metadata = {}
    content_lines = []
    parsing_content = False
    
    for line in lines:
        if line.strip() == '---':
            parsing_content = True
            continue
        if not parsing_content:
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip().lower()] = value.strip()
        else:
            content_lines.append(line)
    
    return metadata, '\n'.join(content_lines)