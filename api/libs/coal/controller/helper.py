import re

def locate_text(df,text,flags=re.IGNORECASE):
    return df[df["text"].str.contains(text,flags=flags)]

def extract_numbers_or_None(str):
    numbers = re.findall(r'\d+\.\d+',str.replace(",","")) + re.findall(r'\d+',str.replace(",",""))
    try:
        return numbers[0]
    except Exception as e:
        return None

def filter_values_only(df):
    df["text"] = df["text"].apply(lambda x: extract_numbers_or_None(x))
    df = df.dropna()
    return df