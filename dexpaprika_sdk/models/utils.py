from pydantic import BaseModel, Field


class Stats(BaseModel):
    """High-level statistics about the DexPaprika ecosystem."""
    
    chains: int = Field(..., description="Number of blockchain networks supported")
    factories: int = Field(..., description="Number of DEX factories or protocols recognized")
    pools: int = Field(..., description="Number of liquidity pools available")
    tokens: int = Field(..., description="Number of tokens recognized across all networks") 