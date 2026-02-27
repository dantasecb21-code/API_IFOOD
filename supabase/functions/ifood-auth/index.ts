import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { corsHeaders } from '../_shared/cors.ts'

serve(async (req) => {
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        const clientId = Deno.env.get('IFOOD_CLIENT_ID')
        const clientSecret = Deno.env.get('IFOOD_CLIENT_SECRET')
        const baseUrl = Deno.env.get('IFOOD_API_BASE_URL') || 'https://merchant-api.ifood.com.br'

        if (!clientId || !clientSecret) {
            throw new Error('IFOOD_CLIENT_ID or IFOOD_CLIENT_SECRET not configured')
        }

        const { grantType = 'client_credentials' } = await req.json()

        const params = new URLSearchParams()
        params.append('grantType', grantType)
        params.append('clientId', clientId)
        params.append('clientSecret', clientSecret)

        const response = await fetch(`${baseUrl}/authentication/v1.0/oauth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: params.toString()
        })

        if (!response.ok) {
            const text = await response.text()
            throw new Error(`iFood auth failed: ${text}`)
        }

        const data = await response.json()

        return new Response(JSON.stringify(data), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200,
        })
    } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 400,
        })
    }
})
