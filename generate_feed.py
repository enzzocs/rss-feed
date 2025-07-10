import base64
from datetime import datetime
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dateutil import parser

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# IDs e nomes
SPREADSHEET_ID = '1WO1JfJMPcCypIUmxbt0Qir8iLDweeOP0NBtp5SmqVZk'
RANGE_NAME = 'Página1!A:E'

# URLs das imagens por urgência (1 = Alta, 2 = Média, 3 = Baixa)
URGENCIA_IMAGENS = {
    "1": "https://enzzocs.github.io/rss-feed/img/urgencia_alta.png",
    "2": "https://enzzocs.github.io/rss-feed/img/urgencia_media.png",
    "3": "https://enzzocs.github.io/rss-feed/img/urgencia_baixa.png"
}

def get_sheet_values():
    creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT')
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    return values

def gerar_feed_xml(rows):
    items = []

    for row in rows[1:]:  # pula o cabeçalho
        try:
            titulo, link, descricao, data_str, urgencia = row
        except ValueError:
            continue

        try:
            dt = parser.parse(data_str)
            pubdate = dt.strftime('%a, %d %b %Y %H:%M:%S +0000')
        except Exception:
            pubdate = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')

        urgencia = urgencia.strip()
        imagem = URGENCIA_IMAGENS.get(urgencia, "")
        descricao_com_img = f"""<![CDATA[
        <img src="{imagem}" style="width:16px;height:16px;" /> {descricao}
        ]]>"""

        item = {
            "urgencia": int(urgencia),
            "xml": f"""
  <item>
    <title>[{urgencia}] {titulo}</title>
    <link>{link}</link>
    <description>{descricao_com_img}</description>
    <pubDate>{pubdate}</pubDate>
    <guid isPermaLink="false">{base64.b64encode(link.encode()).decode()}</guid>
  </item>"""
        }

        items.append(item)

    # Ordena por urgência crescente (1 = Alta prioridade)
    items.sort(key=lambda x: x["urgencia"])

    now = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Anúncios ACP</title>
  <link>https://enzzocs.github.io/rss-feed/</link>
  <description>Feed gerado automaticamente via GitHub Actions</description>
  <lastBuildDate>{now}</lastBuildDate>
  {''.join([item["xml"] for item in items])}
</channel>
</rss>"""

    return feed

def main():
    rows = get_sheet_values()
    feed_xml = gerar_feed_xml(rows)
    with open('feed.xml', 'w', encoding='utf-8') as f:
        f.write(feed_xml)

if __name__ == '__main__':
    main()
