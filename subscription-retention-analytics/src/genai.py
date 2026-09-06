"""
genai.py
--------
GenAI Retention Copilot with structured output, grounding, and validation.

Architecture:
Customer Data → ML Model → Churn Probability → SHAP Drivers → Grounded GenAI → Structured Output

The LLM is NOT allowed to predict churn. It only interprets and communicates
the analytical results that have been validated by the ML pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional, Literal
import json
import os
from abc import ABC, abstractmethod


@dataclass
class CustomerProfile:
    """Validated customer information passed to GenAI."""
    customer_id: str
    contract: str
    tenure_months: int
    monthly_charges: float
    total_charges: float
    internet_service: str
    payment_method: str
    online_security: str
    tech_support: str
    partner: str
    dependents: str
    senior_citizen: int
    paperless_billing: str
    phone_service: str
    multiple_lines: str
    online_backup: str
    device_protection: str
    streaming_tv: str
    streaming_movies: str
    gender: str


@dataclass
class MLResults:
    """Validated ML model outputs passed to GenAI."""
    churn_probability: float
    risk_level: str
    top_drivers: list[dict]  # [{"feature": str, "value": any, "contribution": float, "direction": str}]
    model_type: str
    threshold_used: float


@dataclass
class GenAIResponse:
    """Structured response from GenAI Copilot."""
    risk_level: str
    churn_probability: float
    top_drivers: list[dict]
    evidence: list[str]
    retention_considerations: list[str]
    missing_information: list[str]
    limitations: list[str]
    schema_version: str = "1.0"
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "GenAIResponse":
        data = json.loads(json_str)
        return cls(**data)
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate response structure and content."""
        errors = []
        
        # Required fields
        required = ["risk_level", "churn_probability", "top_drivers", 
                   "evidence", "retention_considerations", "missing_information", "limitations"]
        for field_name in required:
            if field_name not in asdict(self) or getattr(self, field_name) is None:
                errors.append(f"Missing required field: {field_name}")
        
        # Type checks
        if not isinstance(self.risk_level, str):
            errors.append("risk_level must be string")
        if not isinstance(self.churn_probability, (int, float)):
            errors.append("churn_probability must be numeric")
        if not isinstance(self.top_drivers, list):
            errors.append("top_drivers must be list")
        if not isinstance(self.evidence, list):
            errors.append("evidence must be list")
        if not isinstance(self.retention_considerations, list):
            errors.append("retention_considerations must be list")
        if not isinstance(self.missing_information, list):
            errors.append("missing_information must be list")
        if not isinstance(self.limitations, list):
            errors.append("limitations must be list")
        
        # Value checks
        valid_risk_levels = ["Low", "Medium", "High", "Critical"]
        if self.risk_level not in valid_risk_levels:
            errors.append(f"risk_level must be one of {valid_risk_levels}")
        
        if not (0 <= self.churn_probability <= 1):
            errors.append("churn_probability must be between 0 and 1")
        
        return len(errors) == 0, errors


class LLMProvider(ABC):
    """Abstract base for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        pass


class MockLLMProvider(LLMProvider):
    """Mock provider for testing without API keys."""
    
    def generate(self, prompt: str, **kwargs) -> str:
        # Return a valid structured response for testing
        return json.dumps({
            "risk_level": "High",
            "churn_probability": 0.87,
            "top_drivers": [
                {"feature": "Contract", "value": "Month-to-month", "contribution": 0.35, "direction": "increases"},
                {"feature": "tenure", "value": 5, "contribution": 0.28, "direction": "increases"},
                {"feature": "MonthlyCharges", "value": 92.0, "contribution": 0.15, "direction": "increases"}
            ],
            "evidence": [
                "Customer has month-to-month contract (highest churn segment)",
                "Tenure is only 5 months (early tenure danger window)",
                "Monthly charges of $92 are above average"
            ],
            "retention_considerations": [
                "Offer annual contract discount to reduce churn risk",
                "Proactive check-in call to address service concerns",
                "Consider promotional pricing for loyalty"
            ],
            "missing_information": [
                "Customer support interaction history",
                "Network quality in customer's area",
                "Competitor offers in customer's region"
            ],
            "limitations": [
                "Analysis based on model probabilities, not guaranteed outcomes",
                "No access to real-time usage data or support tickets",
                "Retention considerations are suggestions, not guaranteed effective actions"
            ],
            "schema_version": "1.0"
        })


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var.")
    
    def generate(self, prompt: str, **kwargs) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.1),
            max_tokens=kwargs.get("max_tokens", 1500),
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content


class AnthropicProvider(LLMProvider):
    """Anthropic API provider."""
    
    def __init__(self, api_key: str = None, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY env var.")
    
    def generate(self, prompt: str, **kwargs) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)
        
        response = client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1500),
            temperature=kwargs.get("temperature", 0.1),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text


# ============================================================
# PROMPT TEMPLATES
# ============================================================

PROMPT_A_BASIC = """You are a retention analyst. Explain why this customer is at risk of churning.

Customer Profile:
- Contract: {contract}
- Tenure: {tenure_months} months
- Monthly Charges: ${monthly_charges:.2f}
- Total Charges: ${total_charges:.2f}
- Internet Service: {internet_service}
- Payment Method: {payment_method}
- Online Security: {online_security}
- Tech Support: {tech_support}

ML Model Results:
- Churn Probability: {churn_probability:.2%}
- Risk Level: {risk_level}
- Top Model Drivers:
{drivers_text}

Provide a clear, concise explanation of the churn risk factors for this customer."""


PROMPT_B_EVIDENCE_GROUNDED = """You are a retention analyst. Generate an evidence-grounded explanation for this customer's churn risk.

CRITICAL INSTRUCTIONS:
1. Use ONLY the customer information and model results provided below
2. Do NOT invent customer complaints, satisfaction scores, or competitor information
3. Do NOT assume business policies not stated in the data
4. Distinguish clearly between EVIDENCE (from data) and RECOMMENDATIONS (your suggestions)
5. If information is not available, state "Insufficient information from the available customer data"

Customer Profile:
- Contract: {contract}
- Tenure: {tenure_months} months
- Monthly Charges: ${monthly_charges:.2f}
- Total Charges: ${total_charges:.2f}
- Internet Service: {internet_service}
- Payment Method: {payment_method}
- Online Security: {online_security}
- Tech Support: {tech_support}
- Partner: {partner}
- Dependents: {dependents}
- Senior Citizen: {senior_citizen}
- Paperless Billing: {paperless_billing}
- Phone Service: {phone_service}
- Multiple Lines: {multiple_lines}
- Online Backup: {online_backup}
- Device Protection: {device_protection}
- Streaming TV: {streaming_tv}
- Streaming Movies: {streaming_movies}
- Gender: {gender}

ML Model Results:
- Churn Probability: {churn_probability:.2%}
- Risk Level: {risk_level}
- Model Type: {model_type}
- Decision Threshold: {threshold_used:.2f}
- Top Model-Supported Drivers (SHAP contributions):
{drivers_text}

Generate a structured explanation with these sections:
1. EVIDENCE: Facts directly from the customer data and model results
2. MODEL-SUPPORTED DRIVERS: What the model identifies as key risk factors
3. RETENTION CONSIDERATIONS: Suggested actions (clearly labeled as suggestions)
4. MISSING INFORMATION: What would help but isn't in the data
5. LIMITATIONS: Caveats about this analysis"""


PROMPT_C_STRUCTURED = """You are a retention analyst. Generate a STRUCTURED JSON response for this customer's churn risk analysis.

CRITICAL INSTRUCTIONS:
1. Output MUST be valid JSON matching the exact schema below
2. Use ONLY the provided customer data and model results
3. Do NOT invent any facts, complaints, satisfaction scores, competitor info, or business policies
4. Distinguish EVIDENCE (data-supported) from RETENTION CONSIDERATIONS (suggestions)
5. For any missing data, use "Insufficient information from the available customer data"

Customer Profile:
- Contract: {contract}
- Tenure: {tenure_months} months
- Monthly Charges: ${monthly_charges:.2f}
- Total Charges: ${total_charges:.2f}
- Internet Service: {internet_service}
- Payment Method: {payment_method}
- Online Security: {online_security}
- Tech Support: {tech_support}
- Partner: {partner}
- Dependents: {dependents}
- Senior Citizen: {senior_citizen}
- Paperless Billing: {paperless_billing}
- Phone Service: {phone_service}
- Multiple Lines: {multiple_lines}
- Online Backup: {online_backup}
- Device Protection: {device_protection}
- Streaming TV: {streaming_tv}
- Streaming Movies: {streaming_movies}
- Gender: {gender}

ML Model Results:
- Churn Probability: {churn_probability:.2%}
- Risk Level: {risk_level}
- Model Type: {model_type}
- Decision Threshold: {threshold_used:.2f}
- Top Model-Supported Drivers (SHAP):
{drivers_text}

REQUIRED JSON SCHEMA:
{{
  "risk_level": "Low|Medium|High|Critical",
  "churn_probability": 0.0-1.0,
  "top_drivers": [
    {{"feature": "string", "value": "any", "model_supported_contribution": 0.0, "direction": "increases|decreases"}}
  ],
  "evidence": ["string"],  // Data-supported facts only
  "retention_considerations": ["string"],  // Suggested actions, clearly suggestions
  "missing_information": ["string"],  // What's not in the data
  "limitations": ["string"],  // Caveats
  "schema_version": "1.0"
}}"""


def format_drivers_for_prompt(drivers: list[dict]) -> str:
    """Format top drivers for prompt inclusion."""
    lines = []
    for i, d in enumerate(drivers, 1):
        feat = d.get("feature", "Unknown")
        val = d.get("value", "N/A")
        contrib = d.get("contribution", 0)
        direction = d.get("direction", "unknown")
        lines.append(f"  {i}. {feat} = {val} → {direction} risk (SHAP: {contrib:+.3f})")
    return "\n".join(lines) if lines else "  No drivers provided"


def build_prompt(
    profile: CustomerProfile,
    ml_results: MLResults,
    prompt_version: Literal["A", "B", "C"] = "C"
) -> str:
    """Build prompt from template based on version."""
    drivers_text = format_drivers_for_prompt(ml_results.top_drivers)
    
    profile_dict = asdict(profile)
    ml_dict = asdict(ml_results)
    ml_dict["drivers_text"] = drivers_text
    
    if prompt_version == "A":
        template = PROMPT_A_BASIC
    elif prompt_version == "B":
        template = PROMPT_B_EVIDENCE_GROUNDED
    else:
        template = PROMPT_C_STRUCTURED
    
    return template.format(**profile_dict, **ml_dict)


def parse_llm_response(response_text: str) -> GenAIResponse:
    """Parse and validate LLM response."""
    try:
        # Try to extract JSON if wrapped in markdown
        if "```json" in response_text:
            start = response_text.index("```json") + 7
            end = response_text.index("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.index("```") + 3
            end = response_text.index("```", start)
            response_text = response_text[start:end].strip()
        
        response = GenAIResponse.from_json(response_text)
        is_valid, errors = response.validate()
        if not is_valid:
            raise ValueError(f"Validation failed: {errors}")
        return response
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    except Exception as e:
        raise ValueError(f"Response parsing failed: {e}")


class RetentionCopilot:
    """GenAI Retention Copilot - grounded interpretation layer."""
    
    def __init__(
        self,
        provider: LLMProvider,
        prompt_version: Literal["A", "B", "C"] = "C",
        temperature: float = 0.1
    ):
        self.provider = provider
        self.prompt_version = prompt_version
        self.temperature = temperature
    
    def explain_customer(
        self,
        profile: CustomerProfile,
        ml_results: MLResults
    ) -> GenAIResponse:
        """Generate structured explanation for a single customer."""
        prompt = build_prompt(profile, ml_results, self.prompt_version)
        response_text = self.provider.generate(prompt, temperature=self.temperature)
        return parse_llm_response(response_text)
    
    def explain_batch(
        self,
        profiles: list[CustomerProfile],
        ml_results_list: list[MLResults]
    ) -> list[GenAIResponse]:
        """Generate explanations for multiple customers."""
        return [self.explain_customer(p, m) for p, m in zip(profiles, ml_results_list)]


def create_customer_profile(df_row: pd.Series) -> CustomerProfile:
    """Create CustomerProfile from dataframe row."""
    return CustomerProfile(
        customer_id=str(df_row.get("customerID", "")),
        contract=str(df_row.get("Contract", "Unknown")),
        tenure_months=int(df_row.get("tenure", 0)),
        monthly_charges=float(df_row.get("MonthlyCharges", 0)),
        total_charges=float(df_row.get("TotalCharges", 0)),
        internet_service=str(df_row.get("InternetService", "Unknown")),
        payment_method=str(df_row.get("PaymentMethod", "Unknown")),
        online_security=str(df_row.get("OnlineSecurity", "Unknown")),
        tech_support=str(df_row.get("TechSupport", "Unknown")),
        partner=str(df_row.get("Partner", "Unknown")),
        dependents=str(df_row.get("Dependents", "Unknown")),
        senior_citizen=int(df_row.get("SeniorCitizen", 0)),
        paperless_billing=str(df_row.get("PaperlessBilling", "Unknown")),
        phone_service=str(df_row.get("PhoneService", "Unknown")),
        multiple_lines=str(df_row.get("MultipleLines", "Unknown")),
        online_backup=str(df_row.get("OnlineBackup", "Unknown")),
        device_protection=str(df_row.get("DeviceProtection", "Unknown")),
        streaming_tv=str(df_row.get("StreamingTV", "Unknown")),
        streaming_movies=str(df_row.get("StreamingMovies", "Unknown")),
        gender=str(df_row.get("gender", "Unknown"))
    )


def create_ml_results(
    churn_prob: float,
    risk_level: str,
    top_drivers: list[dict],
    model_type: str = "Random Forest",
    threshold: float = 0.5
) -> MLResults:
    """Create MLResults from model outputs."""
    return MLResults(
        churn_probability=churn_prob,
        risk_level=risk_level,
        top_drivers=top_drivers,
        model_type=model_type,
        threshold_used=threshold
    )


if __name__ == "__main__":
    # Test with mock provider
    provider = MockLLMProvider()
    copilot = RetentionCopilot(provider, prompt_version="C")
    
    profile = CustomerProfile(
        customer_id="TEST-001",
        contract="Month-to-month",
        tenure_months=5,
        monthly_charges=92.0,
        total_charges=460.0,
        internet_service="Fiber optic",
        payment_method="Electronic check",
        online_security="No",
        tech_support="No",
        partner="No",
        dependents="No",
        senior_citizen=0,
        paperless_billing="Yes",
        phone_service="Yes",
        multiple_lines="No",
        online_backup="No",
        device_protection="No",
        streaming_tv="No",
        streaming_movies="No",
        gender="Male"
    )
    
    ml_results = MLResults(
        churn_probability=0.87,
        risk_level="Critical",
        top_drivers=[
            {"feature": "Contract", "value": "Month-to-month", "contribution": 0.35, "direction": "increases"},
            {"feature": "tenure", "value": 5, "contribution": 0.28, "direction": "increases"},
            {"feature": "MonthlyCharges", "value": 92.0, "contribution": 0.15, "direction": "increases"}
        ],
        model_type="Random Forest",
        threshold_used=0.5
    )
    
    response = copilot.explain_customer(profile, ml_results)
    print("GenAI Response:")
    print(response.to_json())
    print(f"\nValid: {response.validate()[0]}")