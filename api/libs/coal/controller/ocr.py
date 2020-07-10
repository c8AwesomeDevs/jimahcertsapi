"""Summary
"""
import pytesseract
import pandas as pd
import io


class OCR():

	"""Summary
	"""
	
	def get_ocr_results(self,img):
	    """Summary
	    
	    Args:
	        img (TYPE): Description
	    
	    Returns:
	        TYPE: Description
	    """
	    df_results = pytesseract.image_to_data(img).replace('"',"")
	    df_results_data = io.StringIO(df_results)
	    df_results_df = pd.read_csv(df_results_data, sep="\t")
	    df_results_df = df_results_df.dropna()
	    return df_results_df

	def filter_ocr_results(self,df):
	    """Summary
	    
	    Args:
	        df (TYPE): Description
	    
	    Returns:
	        TYPE: Description
	    """
	    levels = df["level"].drop_duplicates().to_list()
	    pages = df["page_num"].drop_duplicates().to_list()
	    blocks = df["block_num"].drop_duplicates().to_list()
	    paragraphs = df["par_num"].drop_duplicates().to_list()
	    lines = df["line_num"].drop_duplicates().to_list()    
	    
	    ocr_results = []
	    for block in blocks:
	        for paragraph in paragraphs:
	            for line in lines:
	                result_df = df[(df["block_num"]==block) & (df["par_num"]==paragraph) & (df["line_num"]==line)]
	                if not result_df.empty:
	                    min_top = min(result_df["top"].to_list())
	                    min_left = min(result_df["left"].to_list())
	                    #print(result_df["text"].to_list())
	                    expression = " ".join(result_df["text"].apply(lambda x: str(x)).to_list())
	                    #expression = result_df["text"].to_list()
	                    ocr_results.append([block,paragraph,line,min_top,min_left,expression])
	                    
	    ocr_results_df = pd.DataFrame(ocr_results)
	    ocr_results_df.columns = ["block","paragraph","line","top","left","text"]
	    return ocr_results_df