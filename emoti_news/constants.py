_VAR_PREFIX = "EM_NEWS"


class EnvVars:
    """
    List of environment variables used by the application
    """

    PgPassword = f"{_VAR_PREFIX}_PG_PASS"
    JobAdminToken = f"{_VAR_PREFIX}_JOB_ADMIN_TOKEN"

    # NEWS API Sources
    ApiKeyNewsApiOrg = f"{_VAR_PREFIX}_API_NEWSAPI_ORG"
    ApiKeyNewsDataIo = f"{_VAR_PREFIX}_API_NEWSDATA_IO"

    # LLM APIs
    LLMAPITogetherAI = f"{_VAR_PREFIX}_LLM_API_TOGETHER_AI"
