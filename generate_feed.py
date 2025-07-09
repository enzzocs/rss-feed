import base64
from datetime import datetime
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dateutil import parser

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# IDs e nomes
SPREADSHEET_ID = '1WO1JfJMPcCypIUmxbt0Qir8iLDweeOP0NBtp5SmqVZk'  # sua planilha
RANGE_NAME = 'Página1!A:E'  # Título, Link, Descrição, Data, Urgência

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
            continue  # pula linhas incompletas

        try:
            dt = parser.parse(data_str)
            pubdate = dt.strftime('%a, %d %b %Y %H:%M:%S +0000')
        except Exception:
            pubdate = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')

        item = f"""
  <item>
    <title>[{urgencia}] {titulo}</title>
    <link>{link}</link>
    <description>{descricao}</description>
    <pubDate>{pubdate}</pubDate>
    <guid isPermaLink="false">{base64.b64encode(link.encode()).decode()}</guid>
  </item>"""
        items.append(item)

    now = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Anúncios ACP</title>
  <link>https://enzzocs.github.io/rss-feed/</link>
  <description>Feed gerado automaticamente via GitHub Actions</description>
  <lastBuildDate>{now}</lastBuildDate>
  {''.join(items)}
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
