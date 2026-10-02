import json
from pathlib import Path

import anyio.to_thread
from web3 import Web3

from app.core.config import settings
from app.modules.analytics import service as analytics_service
from app.modules.market_data import service as market_data_service
from app.modules.ml import service as ml_service
from app.modules.signals import service as signals_service

ABI_PATH = Path(__file__).parent / "abi" / "StockPrediction.json"


def get_web3() -> Web3:
    web3 = Web3(
        Web3.HTTPProvider(settings.blockchain_rpc_url)
    )

    if not web3.is_connected():
        raise ConnectionError(
            f"Could not connect to Ganache at "
            f"{settings.blockchain_rpc_url}"
        )

    return web3


def load_contract():
    web3 = get_web3()

    if not settings.blockchain_contract_address:
        raise ValueError(
            "Blockchain contract address is not configured."
        )

    with open(
        ABI_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        contract_json = json.load(file)

    abi = contract_json["abi"]

    contract = web3.eth.contract(
        address=Web3.to_checksum_address(
            settings.blockchain_contract_address
        ),
        abi=abi,
    )

    return web3, contract


def get_blockchain_status() -> dict:
    web3, contract = load_contract()

    accounts = web3.eth.accounts

    return {
        "connected": web3.is_connected(),
        "chain_id": web3.eth.chain_id,
        "latest_block": web3.eth.block_number,
        "account": accounts[0] if accounts else None,
        "contract_address": contract.address,
    }


def store_prediction(
    stock_name: str,
    current_price: float,
    predicted_price: float,
    direction: str,
    confidence: float,
    up_probability: float,
    down_probability: float,
    signal_score: float,
    stop_loss: float,
    target_price: float,
) -> dict:
    web3, contract = load_contract()

    accounts = web3.eth.accounts

    if not accounts:
        raise RuntimeError(
            "No Ganache accounts are available."
        )

    sender = accounts[0]

    transaction_hash = (
        contract.functions.addPrediction(
            stock_name,
            round(current_price * 100),
            round(predicted_price * 100),
            direction,
            round(confidence),
            round(up_probability),
            round(down_probability),
            round(signal_score * 100),
            round(stop_loss * 100),
            round(target_price * 100),
        ).transact(
            {
                "from": sender,
            }
        )
    )

    receipt = web3.eth.wait_for_transaction_receipt(
        transaction_hash
    )

    return {
        "transaction_hash": transaction_hash.hex(),
        "block_number": receipt["blockNumber"],
        "status": receipt["status"],
        "contract_address": contract.address,
        "sender": sender,
    }


def get_latest_prediction() -> dict | None:
    """
    Return the latest prediction stored on the entire blockchain.
    """

    _web3, contract = load_contract()

    count = (
        contract.functions
        .getPredictionCount()
        .call()
    )

    if count == 0:
        return None

    prediction = (
        contract.functions
        .getPrediction(count - 1)
        .call()
    )

    return {
        "stock_name": prediction[0],
        "current_price": prediction[1] / 100,
        "predicted_price": prediction[2] / 100,
        "direction": prediction[3],
        "confidence": prediction[4],
        "up_probability": prediction[5],
        "down_probability": prediction[6],
        "signal_score": prediction[7] / 100,
        "stop_loss": prediction[8] / 100,
        "target_price": prediction[9] / 100,
        "timestamp": prediction[10],
    }


def get_latest_prediction_for_stock(
    stock_name: str,
) -> dict | None:
    """
    Find the newest blockchain prediction for one specific stock.

    Example blockchain history:

        TCS.NS
        SBI.NS
        RELIANCE.NS

    Searching for TCS.NS will still return the existing
    TCS.NS prediction instead of only checking RELIANCE.NS.
    """

    _web3, contract = load_contract()

    normalized_stock_name = (
        stock_name
        .strip()
        .upper()
    )

    count = (
        contract.functions
        .getPredictionCount()
        .call()
    )

    if count == 0:
        return None

    # Search from newest prediction to oldest prediction.
    for index in range(
        count - 1,
        -1,
        -1,
    ):
        prediction = (
            contract.functions
            .getPrediction(index)
            .call()
        )

        stored_stock_name = (
            str(prediction[0])
            .strip()
            .upper()
        )

        if stored_stock_name != normalized_stock_name:
            continue

        block_number = None

        # Find the PredictionAdded event belonging to this
        # prediction so we can recover its original block.
        try:
            events = (
                contract.events
                .PredictionAdded()
                .get_logs(
                    from_block=0,
                    to_block="latest",
                    argument_filters={
                        "predictionId": index,
                    },
                )
            )

            if events:
                block_number = events[-1]["blockNumber"]

        except Exception:  # noqa: BLE001 - best-effort block lookup
            # The blockchain prediction itself is still valid
            # even if the event lookup cannot determine the
            # original block number.
            block_number = None

        return {
            "prediction_index": index,
            "stock_name": prediction[0],
            "current_price": prediction[1] / 100,
            "predicted_price": prediction[2] / 100,
            "direction": prediction[3],
            "confidence": prediction[4],
            "up_probability": prediction[5],
            "down_probability": prediction[6],
            "signal_score": prediction[7] / 100,
            "stop_loss": prediction[8] / 100,
            "target_price": prediction[9] / 100,
            "timestamp": prediction[10],
            "block_number": block_number,
        }

    return None


async def store_prediction_from_stockview(
    symbol: str,
) -> dict:
    symbol = symbol.strip().upper()

    # --------------------------------------------------
    # 1. CURRENT MARKET PRICE
    # --------------------------------------------------

    quote = await market_data_service.get_quote(
        symbol
    )

    current_price = float(
        quote["price"]
    )

    # --------------------------------------------------
    # 2. ML PREDICTION
    # --------------------------------------------------

    ml_result = await ml_service.predict(
        symbol,
        use_lstm=False,
    )

    predicted_price = ml_result.get(
        "predicted_price"
    )

    if predicted_price is None:
        predicted_price = current_price

    confidence = float(
        ml_result.get(
            "confidence",
            50.0,
        )
    )

    up_probability = float(
        ml_result.get(
            "up_prob",
            50.0,
        )
    )

    down_probability = float(
        ml_result.get(
            "dn_prob",
            50.0,
        )
    )

    # --------------------------------------------------
    # 3. FINAL STOCKVIEW FUSION SIGNAL
    # --------------------------------------------------

    fusion = await signals_service.get_fusion(
        symbol,
        interval="1d",
        period="2y",
    )

    direction = fusion["final_label"]

    signal_score = float(
        fusion["fused_score"]
    )

    # --------------------------------------------------
    # 4. SUPPORT / RESISTANCE
    # --------------------------------------------------

    sr = (
        await analytics_service
        .get_support_resistance(
            symbol,
            "1d",
            "2y",
        )
    )

    nearest_support = sr.get(
        "nearest_support"
    )

    nearest_resistance = sr.get(
        "nearest_resistance"
    )

    # Prefer StockView's actual support level.
    # Fall back to 2% below price if unavailable.
    stop_loss = (
        float(nearest_support)
        if nearest_support is not None
        else current_price * 0.98
    )

    # Prefer StockView's actual resistance level.
    # Fall back to 3% above price if unavailable.
    target_price = (
        float(nearest_resistance)
        if nearest_resistance is not None
        else current_price * 1.03
    )

    # --------------------------------------------------
    # 5. NORMALIZE VALUES
    # --------------------------------------------------

    normalized_current_price = round(
        current_price,
        2,
    )

    normalized_predicted_price = round(
        float(predicted_price),
        2,
    )

    normalized_confidence = round(confidence)

    normalized_up_probability = round(up_probability)

    normalized_down_probability = round(down_probability)

    normalized_signal_score = round(
        signal_score,
        2,
    )

    normalized_stop_loss = round(
        stop_loss,
        2,
    )

    normalized_target_price = round(
        target_price,
        2,
    )

    # --------------------------------------------------
    # 6. FIND PREVIOUS RECORD FOR THIS SAME STOCK
    # --------------------------------------------------

    latest = await anyio.to_thread.run_sync(
        get_latest_prediction_for_stock,
        symbol,
    )

    if latest is not None:
        is_duplicate = (
            latest["stock_name"].strip().upper()
            == symbol
            and round(
                latest["current_price"],
                2,
            )
            == normalized_current_price
            and round(
                latest["predicted_price"],
                2,
            )
            == normalized_predicted_price
            and latest["direction"]
            == direction
            and latest["confidence"]
            == normalized_confidence
            and latest["up_probability"]
            == normalized_up_probability
            and latest["down_probability"]
            == normalized_down_probability
            and round(
                latest["signal_score"],
                2,
            )
            == normalized_signal_score
            and round(
                latest["stop_loss"],
                2,
            )
            == normalized_stop_loss
            and round(
                latest["target_price"],
                2,
            )
            == normalized_target_price
        )

        # --------------------------------------------------
        # SAME PREDICTION ALREADY EXISTS
        # --------------------------------------------------

        if is_duplicate:
            blockchain_status = await anyio.to_thread.run_sync(
                get_blockchain_status
            )

            return {
                "saved": False,
                "message": (
                    "Prediction already stored "
                    "on blockchain."
                ),
                "transaction_hash": None,
                "block_number": latest.get(
                    "block_number"
                ),
                "status": 1,
                "contract_address": (
                    blockchain_status[
                        "contract_address"
                    ]
                ),
                "sender": (
                    blockchain_status[
                        "account"
                    ]
                ),
            }

    # --------------------------------------------------
    # 7. STORE NEW / CHANGED PREDICTION
    # --------------------------------------------------

    result = await anyio.to_thread.run_sync(
        lambda: store_prediction(
            stock_name=symbol,
            current_price=current_price,
            predicted_price=float(predicted_price),
            direction=direction,
            confidence=confidence,
            up_probability=up_probability,
            down_probability=down_probability,
            signal_score=signal_score,
            stop_loss=stop_loss,
            target_price=target_price,
        )
    )

    return {
        "saved": True,
        "message": (
            "Prediction saved to blockchain."
        ),
        **result,
    }