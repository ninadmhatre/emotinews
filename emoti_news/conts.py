_ENV_VAR_NAME_PREFIX = "EM_NEWS"

class EnvVars:
    PgPassword = f"{_ENV_VAR_NAME_PREFIX}_PG_PASS"
    JobAdminToken = f"{_ENV_VAR_NAME_PREFIX}_JOB_ADMIN_TOKEN"

    # NEWS API Sources
    ApiKeyNewsApiOrg = f"{_ENV_VAR_NAME_PREFIX}_API_NEWSAPI_ORG"
    ApiKeyNewsDataIo = f"{_ENV_VAR_NAME_PREFIX}_API_NEWSDATA_IO"
