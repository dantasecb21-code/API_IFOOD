// CÓDIGO PARA A EDGE FUNCTION: ifood-auth
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const CID = "324b51ec-d3b0-47ff-ab74-e577c0cb3875";
const SEC = "giqwx9pfymnzj6c3u3844wg6i9dxluf814ukh9sdzj07c580dptqx6fjec6wnttobw80o9snvks3nkag25vfhwo3xgmk45r374z";

serve(async (req) => {
    console.log("Tentando login no iFood...");

    const response = await fetch("https://merchant-api.ifood.com.br/authentication/v1.0/oauth/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
            grantType: "client_credentials",
            clientId: CID,
            clientSecret: SEC
        })
    });

    const data = await response.json();

    if (response.ok) {
        return new Response(JSON.stringify({ success: true, token: data.accessToken }), {
            headers: { "Content-Type": "application/json" },
        });
    } else {
        return new Response(JSON.stringify({ success: false, error: data }), {
            status: 401,
            headers: { "Content-Type": "application/json" },
        });
    }
})
