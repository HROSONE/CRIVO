#!/usr/bin/env bash
# Instala o CRIVO.apk no emulador, abre o app, espera o servidor do aparelho e conversa.
# Prints da tela vão para tela_*.png; o log do Android, para logcat.txt.
set -u
adb install -r CRIVO.apk
adb shell am start -n br.crivo.app/.MainActivity
sleep 5
adb exec-out screencap -p > tela_carregando.png || true
adb forward tcp:8765 tcp:8765
ok=""
for i in $(seq 1 90); do
  if curl -s -m 5 http://127.0.0.1:8765/ | grep -q app.js; then ok=1; echo "servidor do app respondeu após ~$((i * 5)) s"; break; fi
  sleep 5
done
adb logcat -d > logcat.txt || true
if [ -z "$ok" ]; then
  adb exec-out screencap -p > tela_erro.png || true
  grep -iE "python|crivo|chaquopy|AndroidRuntime" logcat.txt | tail -150
  echo "o app não subiu o servidor"; exit 1
fi
sleep 10
adb exec-out screencap -p > tela_pagina.png || true
falhou=0
for fala in "oi" "kkkkk" "tô com falta de ar"; do
  corpo=$(python3 -c 'import json,sys; print(json.dumps({"message": sys.argv[1], "history": []}))' "$fala")
  resposta=$(curl -s -m 180 -H 'Content-Type: application/json' -d "$corpo" http://127.0.0.1:8765/api/chat)
  echo "$fala → $(echo "$resposta" | python3 -c 'import json,sys; r=json.load(sys.stdin); print(r["response"][:120], "| voz do modelo:", (r.get("conversation_voice") or {}).get("used"))' 2>/dev/null || echo "$resposta" | head -c 300)"
  echo "$resposta" | grep -q '"response"' || falhou=1
done
adb logcat -d > logcat.txt || true
[ "$falhou" = 0 ] || { echo "a conversa falhou"; exit 1; }
echo "APK OK no emulador"
