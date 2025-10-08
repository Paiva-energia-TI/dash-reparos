import pandas as pd
from io import BytesIO
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.client_credential import ClientCredential

def baixar_excel_sharepoint(secrets):
    credentials = ClientCredential(
        secrets["sharepoint"]["CLIENT_ID"],
        secrets["sharepoint"]["CLIENT_SECRET"]
    )

    ctx = ClientContext(secrets["sharepoint"]["SITE_URL"]).with_credentials(credentials)
    file = ctx.web.get_file_by_server_relative_url(secrets["sharepoint"]["FILE_URL"])
    file_content = BytesIO()
    file.download(file_content).execute_query()
    file_content.seek(0)

    df = pd.read_excel(file_content, sheet_name="Reparos Paiva")
    return df, file
