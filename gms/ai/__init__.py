def init_ai():
    import os

    import frappe

    os.environ["GOOGLE_API_KEY"] = frappe.conf.get("google_api_key")

def init_logfire():
    import logfire
    import os
    import frappe
    import traceback
    
    try:
        # Enable langsmith tracing
        os.environ['LANGSMITH_OTEL_ENABLED'] = 'true'
        os.environ['LANGSMITH_OTEL_ONLY'] = 'true'
        os.environ['LANGSMITH_TRACING'] = 'true'
        os.environ['LOGFIRE_TOKEN'] = frappe.conf.get("logfire_token")
            
        logfire.configure(environment="prod",scrubbing=False)
        print("Logfire Configured")    
    except:
        traceback.print_exception() 


init_logfire()
init_ai()
