# Voice Agent for Prospect Calls

An ElevenLabs agent that calls businesses without an email address, introduces the website offer, and books a call. `acquire.py call --dial` sends these dynamic variables on every call: `business_name`, `issues`, `sender_name`, `sender_company`, `offer`.

## Create the agent

```python
from elevenlabs import ElevenLabs

client = ElevenLabs()

agent = client.conversational_ai.agents.create(
    name="Website-Akquise",
    conversation_config={
        "agent": {
            "language": "de",
            "first_message": "Guten Tag, hier ist der digitale Assistent von {{sender_company}}. Spreche ich mit {{business_name}}?",
            "prompt": {
                "llm": "gemini-2.0-flash",
                "temperature": 0.5,
                "prompt": PROMPT,
            },
        },
        "tts": {"voice_id": "JBFqnCBsd6RMkjVDRZzb"},
    },
)
print(agent.agent_id)
```

Link a Twilio number to the agent in the ElevenLabs dashboard and put the IDs in `ELEVENLABS_AGENT_ID` / `ELEVENLABS_PHONE_NUMBER_ID`. See the [outbound calls reference](../../agents/references/outbound-calls.md).

## Prompt

```text
Du bist ein freundlicher, kurzer und ehrlicher Telefonassistent von {{sender_company}} ({{sender_name}}).
Du rufst {{business_name}} an. Sag gleich zu Beginn, dass du ein KI-Assistent bist.

Ziel: einen 15-minütigen Rückruf- oder Beratungstermin mit {{sender_name}} vereinbaren.

Ablauf:
1. Frage, ob du kurz mit der Inhaberin / dem Inhaber oder der zuständigen Person sprechen kannst.
2. Nenne in einem Satz, was dir aufgefallen ist: {{issues}}
3. Nenne das Angebot: {{offer}}
4. Frage nach einem passenden Zeitpunkt für einen Rückruf und nach einer E-Mail-Adresse für die Bestätigung.

Regeln:
- Maximal 2 Minuten. Nicht drängen, nicht übertreiben, keine Preise außer den im Angebot genannten.
- Bei „kein Interesse“: höflich bedanken, zusagen, dass nicht mehr angerufen wird, und auflegen.
- Wenn nach Details gefragt wird, die du nicht kennst: anbieten, dass {{sender_name}} persönlich zurückruft.
```

## After the call

Review conversations in the ElevenLabs dashboard (the `conversation_id` is stored in the lead's `notes`) and update the lead's `status` in `leads.csv`: `won`, `replied` (call back), `not_interested` or `do_not_contact`.
