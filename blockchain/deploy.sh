#!/usr/bin/env bash
#
# Deploy (or re-deploy) the StockPrediction contract to Ganache and write the
# resulting address into backend/.env.
#
#   ./blockchain/deploy.sh
#
# Run this EVERY time Ganache is restarted. Ganache wipes its chain on
# restart, so the old contract address in backend/.env becomes invalid and
# /api/v1/blockchain/* returns "no code at given address".
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$HERE/../backend/.env"

echo "==> Checking Ganache RPC at http://127.0.0.1:7545 ..."
if ! curl -s -m 5 -X POST -H 'Content-Type: application/json' \
      --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
      http://127.0.0.1:7545 | grep -q '"result"'; then
    echo "ERROR: Ganache is not reachable on http://127.0.0.1:7545" >&2
    echo "       Start it first:  docker compose -f backend/docker-compose.yml up -d ganache" >&2
    exit 1
fi

echo "==> Compiling + migrating (truffle) ..."
OUTPUT="$(cd "$HERE" && truffle migrate --reset --network development 2>&1)"
printf '%s\n' "$OUTPUT" | sed -n '/Deploying/,/Saving artifacts/p'

ADDRESS="$(printf '%s\n' "$OUTPUT" \
  | grep -oE 'contract address:[[:space:]]+0x[a-fA-F0-9]{40}' \
  | grep -oE '0x[a-fA-F0-9]{40}' \
  | tail -n 1)"

if [ -z "$ADDRESS" ]; then
    echo "ERROR: could not parse the contract address from truffle output." >&2
    exit 1
fi

echo "==> Contract address: $ADDRESS"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE not found." >&2
    exit 1
fi

if grep -q '^SV_BLOCKCHAIN_CONTRACT_ADDRESS=' "$ENV_FILE"; then
    # BSD/GNU sed compatible in-place edit.
    python3 - "$ENV_FILE" "$ADDRESS" <<'PY'
import re, sys
path, address = sys.argv[1], sys.argv[2]
text = open(path, encoding="utf-8").read()
text = re.sub(
    r"^SV_BLOCKCHAIN_CONTRACT_ADDRESS=.*$",
    f"SV_BLOCKCHAIN_CONTRACT_ADDRESS={address}",
    text,
    flags=re.MULTILINE,
)
open(path, "w", encoding="utf-8").write(text)
PY
else
    printf '\nSV_BLOCKCHAIN_CONTRACT_ADDRESS=%s\n' "$ADDRESS" >> "$ENV_FILE"
fi

echo "==> Wrote SV_BLOCKCHAIN_CONTRACT_ADDRESS into backend/.env"
echo "==> Done. Restart the backend so it picks up the new address."
