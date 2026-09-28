"""
Comprehensive Dataset Generator for the 11-Micro-Agent Architecture in Magnas AI.
Generates domain-specific training examples for each specialized agent.
"""

# 1. Router Agent Domains
ROUTER_DOMAINS = [
    "DOMAIN_OS",
    "DOMAIN_BROWSER",
    "DOMAIN_IDE",
    "DOMAIN_RESUME",
    "DOMAIN_SECURITY",
    "DOMAIN_DATABASE",
    "DOMAIN_VISION_MEDIA",
    "DOMAIN_SCHEDULER",
    "DOMAIN_CLI",
    "DOMAIN_LLM"
]

# Domain-specific datasets
OS_DATASET = [
    ("open chrome", "OPEN_APP"),
    ("launch notepad", "OPEN_APP"),
    ("close firefox", "CLOSE_APP"),
    ("kill calc process", "CLOSE_APP"),
    ("search files matching resume", "SEARCH_FILES"),
    ("find file notes.txt", "SEARCH_FILES"),
    ("list directory in documents", "READ_FILE"),
    ("increase volume by 20 percent", "CHANGE_VOLUME"),
    ("mute volume", "CHANGE_VOLUME"),
    ("take a screenshot", "TAKE_SCREENSHOT"),
    ("type text hello world", "TYPE_TEXT"),
    ("press key enter", "PRESS_KEY")
]

BROWSER_DATASET = [
    ("open website https://google.com", "OPEN_WEBSITE"),
    ("search youtube for synthwave music", "SEARCH_WEB"),
    ("search github for react repositories", "SEARCH_WEB"),
    ("read documentation at https://docs.python.org", "READ_WEB_DOCUMENTATION"),
    ("fetch docs from https://fastapi.tiangolo.com", "READ_WEB_DOCUMENTATION"),
    ("login to platform https://app.example.com", "AUTOMATE_PLATFORM_LOGIN"),
    ("create account on https://portal.site.com", "AUTOMATE_PLATFORM_LOGIN")
]

IDE_DATASET = [
    ("develop a react project using antigravity ide", "DEVELOP_PROJECT_ANTIGRAVITY"),
    ("build python web app in antigravity ide chat", "DEVELOP_PROJECT_ANTIGRAVITY"),
    ("tell antigravity ide to create task manager", "DEVELOP_PROJECT_ANTIGRAVITY"),
    ("run build and test unit tests", "RUN_BUILD_TEST"),
    ("git commit and push changes to main", "GIT_WORKFLOW")
]

RESUME_DATASET = [
    ("design my resume for full stack java developer", "DESIGN_RESUME"),
    ("create resume for sde role", "DESIGN_RESUME"),
    ("build resume for ai engineer", "DESIGN_RESUME"),
    ("analyze my previous resume pdf", "ANALYZE_PREVIOUS_RESUME"),
    ("gather my linkedin profile experience", "GATHER_LINKEDIN_PROFILE")
]

SECURITY_DATASET = [
    ("check policy risk for command", "CHECK_POLICY_RISK"),
    ("view activity and security audit logs", "VIEW_AUDIT_LOGS"),
    ("approve human intervention ticket", "APPROVE_TICKET"),
    ("reject pending approval ticket", "REJECT_TICKET")
]

DATABASE_DATASET = [
    ("query database select from tasks", "QUERY_DATABASE"),
    ("inspect sqlite database schema", "QUERY_DATABASE"),
    ("export audit logs to csv", "EXPORT_DATA"),
    ("export tasks table to markdown", "EXPORT_DATA"),
    ("backup database magnas.db", "BACKUP_DATABASE")
]

VISION_MEDIA_DATASET = [
    ("read screen text ocr screenshot", "READ_SCREEN_TEXT"),
    ("extract text from screen image", "READ_SCREEN_TEXT"),
    ("analyze image dimensions and format", "ANALYZE_IMAGE"),
    ("play pause media playback", "MEDIA_PLAYBACK"),
    ("skip to next track", "MEDIA_PLAYBACK")
]

SCHEDULER_DATASET = [
    ("set timer reminder for meeting in 60 seconds", "SET_TIMER_REMINDER"),
    ("remind me to take break in 10 minutes", "SET_TIMER_REMINDER"),
    ("schedule daily cron automation task", "SCHEDULE_DAILY_CRON"),
    ("cancel scheduled task timer_1234", "CANCEL_SCHEDULED_TASK")
]

CLI_DATASET = [
    ("run powershell command Get-Process", "RUN_POWERSHELL_CMD"),
    ("execute powershell script Get-Service", "RUN_POWERSHELL_CMD"),
    ("run npm install package", "PACKAGE_MANAGER_OPS"),
    ("run pip install torch", "PACKAGE_MANAGER_OPS"),
    ("check network host ping google.com", "NETWORK_DIAGNOSTICS"),
    ("check open port 8787", "NETWORK_DIAGNOSTICS")
]

LLM_DATASET = [
    ("route prompt to local ollama llama3", "ROUTE_LLM_PROMPT"),
    ("ask llm to reason about complex problem", "ROUTE_LLM_PROMPT"),
    ("summarize context text documentation", "SUMMARIZE_CONTEXT"),
    ("compress long documentation prompt", "SUMMARIZE_CONTEXT")
]

AGENT_DATASETS = {
    "os_agent": OS_DATASET,
    "browser_agent": BROWSER_DATASET,
    "ide_agent": IDE_DATASET,
    "resume_agent": RESUME_DATASET,
    "security_agent": SECURITY_DATASET,
    "database_agent": DATABASE_DATASET,
    "vision_agent": VISION_MEDIA_DATASET,
    "scheduler_agent": SCHEDULER_DATASET,
    "cli_agent": CLI_DATASET,
    "llm_agent": LLM_DATASET
}
