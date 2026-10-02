from pydantic import BaseModel, Field


class BlockchainPredictionRequest(BaseModel):
    stock_name: str
    current_price: float
    predicted_price: float
    direction: str
    confidence: float
    up_probability: float
    down_probability: float
    signal_score: float
    stop_loss: float
    target_price: float


class BlockchainPredictionResponse(BaseModel):
    transaction_hash: str
    block_number: int
    status: int
    contract_address: str
    sender: str


class BlockchainLatestPredictionResponse(BaseModel):
    stock_name: str
    current_price: float
    predicted_price: float
    direction: str
    confidence: int
    up_probability: int
    down_probability: int
    signal_score: float
    stop_loss: float
    target_price: float
    timestamp: int


class BlockchainAutoSaveRequest(BaseModel):
    symbol: str = Field(
        ...,
        min_length=1,
        max_length=30,
        examples=["INFY.NS"],
    )


class BlockchainAutoSaveResponse(BaseModel):
    saved: bool
    message: str
    transaction_hash: str | None = None
    block_number: int | None = None
    status: int | None = None
    contract_address: str
    sender: str | None = None


class BlockchainStatusResponse(BaseModel):
    connected: bool
    chain_id: int
    latest_block: int
    account: str | None
    contract_address: str
