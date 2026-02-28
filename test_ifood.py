import httpx
import asyncio

async def test_keys():
    cid = "324b51ec-d3b0-47ff-ab74-e577c0cb3875"
    sec = "giqwx9pfymnzj6c3u3844wg6i9dxluf814ukh9sdzj07c580dptqx6fjec6wnttobw80o9snvks3nkag25vfhwo3xgmk45r374z"
    
    print("--- DIAGNOSTICO IFOOD ---")
    print(f"Testando ID: {cid}")
    
    url = "https://merchant-api.ifood.com.br/authentication/v1.0/oauth/token"
    payload = {
        "grantType": "client_credentials",
        "clientId": cid,
        "clientSecret": sec
    }
    
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(url, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=15)
            print(f"Status Code: {r.status_code}")
            print(f"Resposta bruta: {r.text}")
            if r.status_code == 200:
                print("SUCCESS: CHAVES VALIDAS!")
            else:
                print("FAIL: CHAVES REJEITADAS PELA API.")
        except Exception as e:
            print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_keys())
