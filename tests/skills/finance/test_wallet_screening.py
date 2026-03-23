import pytest
import os
from unittest.mock import patch, MagicMock
from skillware.core.loader import SkillLoader

def get_skill():
    bundle = SkillLoader.load_skill("finance/wallet_screening")
    # Initialize without needing real API keys
    return bundle['module'].WalletScreeningSkill()

@patch("skills.finance.wallet_screening.skill.requests.get")
def test_wallet_screening_success(mock_get):
    skill = get_skill()
    skill.etherscan_api_key = "dummy_key"
    
    # Mock responses
    mock_eth_balance = MagicMock()
    mock_eth_balance.json.return_value = {"status": "1", "result": "1000000000000000000"} # 1 ETH
    
    mock_txs = MagicMock()
    mock_txs.json.return_value = {"status": "1", "result": [
        {"from": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045".lower(), "to": "0x123", "value": "500000000000000000", "isError": "0", "gasUsed": "21000", "gasPrice": "1000000000"}
    ]}
    
    mock_price = MagicMock()
    mock_price.json.return_value = {"ethereum": {"usd": 2000.0, "eur": 1800.0}}
    
    # Configure mock side_effect based on URL/params
    def get_side_effect(url, **kwargs):
        if "action" in kwargs.get("params", {}):
            if kwargs["params"]["action"] == "balance":
                return mock_eth_balance
            elif kwargs["params"]["action"] == "txlist":
                return mock_txs
        return mock_price
    
    mock_get.side_effect = get_side_effect
    
    result = skill.execute({"address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"})
    
    assert "error" not in result
    assert "summary" in result
    assert result["summary"]["balance_eth"] == 1.0
    assert result["summary"]["balance_usd"] == 2000.0
    assert "financial_analysis" in result
    assert result["financial_analysis"]["value_out_eth"] == 0.5 

def test_wallet_screening_invalid_address():
    skill = get_skill()
    result = skill.execute({"address": "invalid_addr"})
    assert "error" in result
    assert "Invalid Ethereum address" in result["error"]
    
def test_wallet_screening_missing_key():
    skill = get_skill()
    skill.etherscan_api_key = None
    result = skill.execute({"address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"})
    assert "error" in result
    assert "Missing ETHERSCAN_API_KEY" in result["error"]
