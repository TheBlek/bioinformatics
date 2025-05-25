import re

def extract_mapped_percentage(file_content):
    # Split content into lines
    lines = file_content.strip().split('\n')
    
    # Search for line containing 'mapped' and a percentage
    for line in lines:
        if 'mapped' in line and '%' in line:
            # Extract percentage using regex
            match = re.search(r'\((\d+\.\d+)%', line)
            if match:
                return float(match.group(1))
    return None
