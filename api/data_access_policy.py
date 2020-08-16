from rest_access_policy import AccessPolicy

class PIDataAccessPolicy(AccessPolicy):

    """Data Access Policy Configuration Class for Application Views.
    
    Attributes:
        statements (List): PI Data Access Policy Configuration statements.
    """
    
    statements = [
        {
            "action": ["get_user_groups","extract_data","view_data","save_edited_data","upload_certificate_data","upload_manual_data","test_pi_connection","view_pdf","preview_configuration_api","extract_manual_log_template"],
            "principal": ["group:data_validator"],
            "effect": "allow"            
        },
        {
            "action": ["get_user_groups","extract_data","view_pdf"],
            "principal": ["group:data_validator","group:certificate_uploader"],
            "effect": "allow"            
        }
    ]