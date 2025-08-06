import asyncio
import json
import sys

# Assurer que le projet courant est dans le PYTHONPATH
if "." not in sys.path:
    sys.path.insert(0, ".")

from services.groq_service import GroqService  # noqa: E402


async def main():
    try:
        svc = GroqService()
        print("GroqService OK")
    except Exception as e:
        print("INIT_ERR:", e)
        return

    # Ping JSON strict minimal (réponse attendue: JSON exact)
    prompt = 'Réponds UNIQUEMENT avec ce JSON exact: {"ping": "pong", "ok": true}'

    try:
        # Si l'implémentation expose un appel interne bas-niveau, on le préfère pour un ping direct
        if hasattr(svc, "_call_groq"):
            res = await svc._call_groq(prompt)
        else:
            # Fallback: utiliser la méthode publique avec un contenu minimal
            res = await svc.structure_job_data("PING", "https://local.test/ping", "test")
        print("CALL_OK")
        if isinstance(res, str):
            try:
                data = json.loads(res)
            except Exception:
                data = {"_raw": res}
        else:
            data = res
        # Affiche seulement un extrait pour éviter d'inonder la console
        print("RESP:", json.dumps(data, ensure_ascii=False)[:400])
    except Exception as e:
        print("CALL_ERR:", e)


if __name__ == "__main__":
    asyncio.run(main())