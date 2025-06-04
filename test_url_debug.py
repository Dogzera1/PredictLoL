import asyncio
import aiohttp

async def test_urls():
    headers = {'x-api-key': '0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z'}
    
    urls = [
        'https://esports-api.lolesports.com/persisted/gw/getLive',
        'https://esports-api.lolesports.com/getLive'
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url, headers=headers, params={'hl': 'pt-BR'}) as resp:
                    print(f'{url}: {resp.status}')
                    if resp.status == 200:
                        data = await resp.json()
                        events = data.get('data', {}).get('schedule', {}).get('events', [])
                        print(f'  Eventos: {len(events)}')
                    else:
                        error_text = await resp.text()
                        print(f'  Erro: {error_text}')
            except Exception as e:
                print(f'{url}: Erro - {e}')

asyncio.run(test_urls()) 
