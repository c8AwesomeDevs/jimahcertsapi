#Search for Cert Types
keys = {
    "cosa_cert": "CERTIFICATE OF SAMPLING AND ANALYSIS",
    "coa_cert": "CERTIFICATE OF ANALYSIS",
    "cosa_cert_att": "ULTIMATE ANALYSIS"
}

#header_guess = image.crop((0,0,1650,500))
footer_guess = None

class Classifier():
    def __init__(self,ocr):
        self.ocr = ocr
    def classify_pages_based_on_keys(self,images,keys={}):
        mapping = {}
        
        for key in keys:
            mapping[key] = []
        
        for image in images:
            header_guess = image.crop((0,0,1650,500))
            ocr_results_df = self.ocr.get_ocr_results(header_guess)
            ocr_results_filtered = self.ocr.filter_ocr_results(ocr_results_df)
            for key in keys:
                is_key = not ocr_results_filtered[ocr_results_filtered["text"].str.contains(keys[key])].empty
                if is_key:
                    mapping[key].append(image)
                    '''plt.figure()
                    plt.title("Certificate of Sampling and Analysis",fontdict={"fontsize":30})
                    plt.imshow(image)'''
                    
        return mapping