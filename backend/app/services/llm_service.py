"""
LLM Service - Generates clinician-facing explanations of triage decisions using Hugging Face Qwen SLM.
"""
import logging
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Fallback template generator if API is unavailable or token is missing
def get_template_explanation(assessment_data: Dict[str, Any]) -> str:
    priority = assessment_data.get("priority", "UNKNOWN")
    risk_score = assessment_data.get("risk_score", 0.0)
    safety_flags = assessment_data.get("safety_flags", [])
    reasons = assessment_data.get("reasons", [])
    deteriorating = assessment_data.get("deteriorating", False)
    
    # Format simple narrative
    summary_parts = []
    
    # Priority & Floor explanation
    if priority == "CRITICAL":
        summary_parts.append("Patient prioritized as CRITICAL due to life-threatening indicators.")
    elif priority == "HIGH":
        summary_parts.append("Patient classified as HIGH risk, requiring urgent evaluation.")
    elif priority == "MODERATE":
        summary_parts.append("Patient classified as MODERATE priority; vitals are borderline.")
    else:
        summary_parts.append("Patient classified as LOW priority; vitals are stable.")

    # Vitals & Safety flags
    if safety_flags:
        summary_parts.append(f"Safety flags triggered: {', '.join([str(f).replace('_', ' ') for f in safety_flags])}.")

    # Deterioration
    if deteriorating:
        summary_parts.append("Vitals show a deteriorating downward trajectory.")

    # Core reasons
    if reasons:
        reason_msgs = [r.get("message") for r in reasons if r.get("message")]
        if reason_msgs:
            summary_parts.append(f"Key indicators include: {'; '.join(reason_msgs[:2])}.")

    summary_parts.append(f"Calculated risk score is {risk_score:.0f}/100. Clinician review required.")
    return " ".join(summary_parts)


def explain_decision(assessment_data: Dict[str, Any]) -> str:
    """
    Generate natural language explanation from structured triage decision.
    Queries Qwen on Hugging Face Serverless Inference API.
    """
    hf_token = getattr(settings, "HF_API_TOKEN", None)
    # Get model ID, default to Qwen 2.5 1.5B Instruct for speed and reliability
    model_id = getattr(settings, "HF_MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct")

    if not hf_token or hf_token.strip() == "" or hf_token == "hf_placeholder":
        logger.info("HF_API_TOKEN not configured or placeholder - using local template explanation")
        return get_template_explanation(assessment_data)

    patient_name = assessment_data.get("patient_name", "Unknown Patient")
    patient_age = assessment_data.get("patient_age", "N/A")
    patient_gender = assessment_data.get("patient_gender", "N/A")
    priority = assessment_data.get("priority", "UNKNOWN")
    safety_floor = assessment_data.get("safety_floor")
    safety_flags = assessment_data.get("safety_flags", [])
    risk_score = assessment_data.get("risk_score", 0.0)
    reasons = assessment_data.get("reasons", [])
    deteriorating = assessment_data.get("deteriorating", False)
    deterioration_severity = assessment_data.get("deterioration_severity")

    # Format reasons
    reasons_text = "; ".join([r.get("message", r.get("code", "")) for r in reasons])

    # Build prompt
    prompt = (
        f"<|im_start|>system\n"
        f"You are a clinical decision explainer. You translate structured triage rules, risk factors, and vital trajectories "
        f"into a clear, concise clinician-facing explanation. DO NOT make clinical diagnoses or alter the priority level. "
        f"Keep the summary strictly under 3 sentences and speak directly to a clinician.\n"
        f"<|im_end|>\n"
        f"<|im_start|>user\n"
        f"Generate an explanation for this structured decision:\n"
        f"- Patient: {patient_name} (Age: {patient_age}, Gender: {patient_gender})\n"
        f"- Triage Priority: {priority} (Safety Floor: {safety_floor or 'None'})\n"
        f"- Risk ML Score: {risk_score:.0f}/100\n"
        f"- Active Safety Flags: {', '.join(safety_flags) if safety_flags else 'None'}\n"
        f"- Vital Sign Issues: {reasons_text}\n"
        f"- Deterioration Status: {'Yes' if deteriorating else 'No'} (Severity: {deterioration_severity or 'N/A'})\n"
        f"Provide the explanation.\n"
        f"<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )

    try:
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {
            "Authorization": f"Bearer {hf_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 150,
                "temperature": 0.2,
                "top_p": 0.9,
                "return_full_text": False
            }
        }
        
        logger.info(f"Querying HF Qwen Model ({model_id}) for explanation...")
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                # Serverless API returns either list of results or dict
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    text = result.get("generated_text", "")
                else:
                    text = ""
                
                # Strip helper tags if Qwen includes them
                explanation = text.strip().replace("<|im_end|>", "").replace("<|im_start|>", "")
                if explanation:
                    logger.info("Explanation generated successfully by Qwen.")
                    return explanation
            
            logger.warning(f"HF API returned status {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Failed to query Hugging Face Inference API: {e}", exc_info=True)

    logger.info("Falling back to local template explanation.")
    return get_template_explanation(assessment_data)
