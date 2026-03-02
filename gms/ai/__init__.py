def init_ai():
    import os

    import frappe

    os.environ["GOOGLE_API_KEY"] = frappe.conf.get("google_api_key")

def init_logfire():
    import os
    import frappe
    import traceback
    
    try:
        import logfire
        # Enable langsmith tracing
        os.environ['LANGSMITH_OTEL_ENABLED'] = 'true'
        os.environ['LANGSMITH_OTEL_ONLY'] = 'true'
        os.environ['LANGSMITH_TRACING'] = 'true'
        os.environ['LOGFIRE_TOKEN'] = frappe.conf.get("logfire_token")
            
        logfire.configure(environment="prod",scrubbing=False)
        print("Logfire Configured")    
    except ImportError:
        print("Logfire module not found. Skipping logfire configuration.")
    except Exception:
        traceback.print_exc() 


init_logfire()
init_ai()
