"""Summary
"""
import re

def locate_text(df,text,flags=re.IGNORECASE):
    """Summary
    
    Args:
        df (TYPE): Description
        text (TYPE): Description
        flags (TYPE, optional): Description
    
    Returns:
        TYPE: Description
    """
    return df[df["text"].str.contains(text,flags=flags)]

def extract_numbers_or_None(str):
    """Summary
    
    Args:
        str (TYPE): Description
    
    Returns:
        TYPE: Description
    """
    numbers = re.findall(r'\d+\.\d+',str.replace(",","")) + re.findall(r'\d+',str.replace(",",""))
    try:
        return numbers[0]
    except Exception as e:
        return None

def filter_values_only(df):
    """Summary
    
    Args:
        df (TYPE): Description
    
    Returns:
        TYPE: Description
    """
    df["text"] = df["text"].apply(lambda x: extract_numbers_or_None(x))
    df = df.dropna()
    return df