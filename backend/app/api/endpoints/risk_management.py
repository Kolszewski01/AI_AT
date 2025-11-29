"""
Risk Management API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()


class RiskCalculationRequest(BaseModel):
    """Risk calculation request model"""
    account_size: float = Field(..., gt=0, description="Account size in USD")
    entry_price: float = Field(..., gt=0, description="Entry price")
    stop_loss: float = Field(..., gt=0, description="Stop loss price")
    risk_percent: float = Field(..., gt=0, le=100, description="Risk percentage (0-100)")
    take_profit: Optional[float] = Field(None, gt=0, description="Take profit price (optional)")
    symbol: str = Field(..., description="Trading symbol")


class RiskCalculationResponse(BaseModel):
    """Risk calculation response model"""
    symbol: str
    account_size: float
    risk_amount: float
    position_size: float
    potential_loss: float
    potential_profit: Optional[float]
    risk_reward_ratio: Optional[float]
    leverage: Optional[float]
    risk_percent: float
    is_safe: bool
    warnings: list[str]


@router.post("/calculate", response_model=RiskCalculationResponse)
async def calculate_risk(request: RiskCalculationRequest):
    """
    Calculate position size and risk parameters

    Args:
        request: Risk calculation parameters

    Returns:
        Risk calculation results with position size, SL/TP, and warnings
    """
    try:
        # Calculate risk amount
        risk_amount = request.account_size * (request.risk_percent / 100)

        # Calculate price difference
        is_long = request.entry_price > request.stop_loss
        price_diff = abs(request.entry_price - request.stop_loss)

        # Calculate position size
        # Position size = Risk amount / Price difference
        position_size = risk_amount / price_diff

        # Calculate potential loss
        potential_loss = position_size * price_diff

        # Calculate potential profit (if TP provided)
        potential_profit = None
        risk_reward_ratio = None
        if request.take_profit:
            tp_diff = abs(request.take_profit - request.entry_price)
            potential_profit = position_size * tp_diff
            risk_reward_ratio = tp_diff / price_diff if price_diff > 0 else 0

        # Calculate leverage (if position value > account size)
        position_value = position_size * request.entry_price
        leverage = position_value / request.account_size if request.account_size > 0 else None

        # Generate warnings
        warnings = []
        is_safe = True

        if request.risk_percent > 2:
            warnings.append(f"High risk! Risking {request.risk_percent}% per trade is dangerous. Recommended: 1-2%")
            is_safe = False

        if leverage and leverage > 10:
            warnings.append(f"High leverage ({leverage:.1f}x) detected! This increases risk significantly.")
            is_safe = False

        if risk_reward_ratio and risk_reward_ratio < 1.5:
            warnings.append(f"Low risk:reward ratio ({risk_reward_ratio:.2f}). Aim for 1:2 or better.")

        if position_value > request.account_size * 0.5:
            warnings.append("Position size is over 50% of account. Consider reducing exposure.")
            is_safe = False

        # SL too close warning
        sl_distance_percent = (price_diff / request.entry_price) * 100
        if sl_distance_percent < 0.5:
            warnings.append(f"Stop loss very close ({sl_distance_percent:.2f}%). May get stopped out easily.")
        elif sl_distance_percent > 10:
            warnings.append(f"Stop loss very far ({sl_distance_percent:.2f}%). Consider tightening.")

        return RiskCalculationResponse(
            symbol=request.symbol,
            account_size=request.account_size,
            risk_amount=round(risk_amount, 2),
            position_size=round(position_size, 6),
            potential_loss=round(potential_loss, 2),
            potential_profit=round(potential_profit, 2) if potential_profit else None,
            risk_reward_ratio=round(risk_reward_ratio, 2) if risk_reward_ratio else None,
            leverage=round(leverage, 2) if leverage else None,
            risk_percent=request.risk_percent,
            is_safe=is_safe,
            warnings=warnings
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PositionSizingRequest(BaseModel):
    """Position sizing request"""
    account_size: float = Field(..., gt=0)
    risk_percent: float = Field(..., gt=0, le=10)
    entry_price: float = Field(..., gt=0)
    stop_loss_percent: float = Field(..., gt=0, description="Stop loss as percentage from entry")


@router.post("/position-size")
async def calculate_position_size(request: PositionSizingRequest):
    """
    Calculate position size based on risk percentage

    Args:
        request: Position sizing parameters

    Returns:
        Position size and related metrics
    """
    try:
        # Calculate stop loss price
        stop_loss_price = request.entry_price * (1 - request.stop_loss_percent / 100)

        # Calculate risk amount
        risk_amount = request.account_size * (request.risk_percent / 100)

        # Calculate position size
        price_diff = request.entry_price - stop_loss_price
        position_size = risk_amount / price_diff

        # Calculate position value
        position_value = position_size * request.entry_price

        # Calculate percentage of account
        account_percent = (position_value / request.account_size) * 100

        return {
            "position_size": round(position_size, 6),
            "position_value": round(position_value, 2),
            "stop_loss_price": round(stop_loss_price, 2),
            "risk_amount": round(risk_amount, 2),
            "account_percent": round(account_percent, 2),
            "is_safe": account_percent <= 50 and request.risk_percent <= 2
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PortfolioRiskRequest(BaseModel):
    """Portfolio risk assessment request"""
    account_size: float
    open_positions: list[dict]


@router.post("/portfolio-risk")
async def assess_portfolio_risk(request: PortfolioRiskRequest):
    """
    Assess total portfolio risk

    Args:
        request: Portfolio with open positions

    Returns:
        Total risk metrics and warnings
    """
    try:
        total_risk = 0
        total_exposure = 0
        position_count = len(request.open_positions)

        for position in request.open_positions:
            position_risk = position.get('risk_amount', 0)
            position_value = position.get('position_value', 0)
            total_risk += position_risk
            total_exposure += position_value

        risk_percent = (total_risk / request.account_size) * 100 if request.account_size > 0 else 0
        exposure_percent = (total_exposure / request.account_size) * 100 if request.account_size > 0 else 0

        warnings = []
        if risk_percent > 5:
            warnings.append(f"Total portfolio risk is {risk_percent:.1f}%. Recommended: under 5%")

        if exposure_percent > 80:
            warnings.append(f"High exposure: {exposure_percent:.1f}% of account")

        if position_count > 5:
            warnings.append(f"Many open positions ({position_count}). Difficult to manage risk.")

        return {
            "account_size": request.account_size,
            "position_count": position_count,
            "total_risk": round(total_risk, 2),
            "total_exposure": round(total_exposure, 2),
            "risk_percent": round(risk_percent, 2),
            "exposure_percent": round(exposure_percent, 2),
            "is_safe": risk_percent <= 5 and exposure_percent <= 80,
            "warnings": warnings
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommended-settings")
async def get_recommended_settings():
    """
    Get recommended risk management settings

    Returns:
        Best practice risk management parameters
    """
    return {
        "risk_per_trade": {
            "conservative": 0.5,
            "moderate": 1.0,
            "aggressive": 2.0,
            "max_recommended": 2.0
        },
        "position_sizing": {
            "max_single_position": 20,  # % of account
            "max_total_exposure": 80     # % of account
        },
        "risk_reward": {
            "minimum": 1.5,
            "recommended": 2.0,
            "optimal": 3.0
        },
        "leverage": {
            "conservative": 2,
            "moderate": 5,
            "aggressive": 10,
            "max_safe": 10
        },
        "portfolio": {
            "max_correlated_positions": 3,
            "max_total_positions": 5,
            "max_portfolio_risk": 5  # % of account
        },
        "stop_loss": {
            "min_distance_percent": 0.5,
            "max_distance_percent": 10,
            "recommended_percent": 2
        }
    }
