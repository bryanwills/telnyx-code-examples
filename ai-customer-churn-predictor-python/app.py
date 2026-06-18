#!/usr/bin/env python3
"""AI Customer Churn Predictor — analyze call/message patterns via Telnyx APIs, AI predicts churn risk and suggests interventions."""
import os, json, time, requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
predictions = []

def call_inference(messages, max_tokens=400):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.2}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

@app.route("/predict", methods=["POST"])
def predict_churn():
    data = request.get_json()
    customer = data
    prompt = f"""Analyze this customer's communication pattern for churn risk. Customer data:
- Monthly call volume trend: {customer.get('call_volumes', [])}
- Monthly message volume trend: {customer.get('message_volumes', [])}
- Support tickets last 90 days: {customer.get('support_tickets', 0)}
- Account age months: {customer.get('account_age_months', 0)}
- Contract renewal in days: {customer.get('renewal_days', 'unknown')}
- Last login days ago: {customer.get('last_login_days', 0)}
- Payment issues: {customer.get('payment_issues', 0)}

Return JSON: churn_risk (high/medium/low), probability (0.0-1.0), risk_factors (list of strings), recommended_actions (list of specific interventions), urgency (immediate/this_week/this_month), estimated_revenue_at_risk (string)."""
    try:
        result = call_inference([{"role": "system", "content": "You are a customer success analyst specializing in telecom churn prediction."}, {"role": "user", "content": prompt}])
        prediction = json.loads(result)
        prediction["customer_id"] = customer.get("customer_id", f"CUST-{int(time.time())}")
        prediction["predicted_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        predictions.append(prediction)
        return jsonify(prediction), 200
    except json.JSONDecodeError:
        return jsonify({"raw": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/predict/batch", methods=["POST"])
def batch_predict():
    data = request.get_json()
    customers = data.get("customers", [])
    results = []
    for c in customers[:20]:
        try:
            resp = predict_churn_internal(c)
            results.append(resp)
        except Exception:
            results.append({"customer_id": c.get("customer_id"), "error": "prediction failed"})
    high_risk = [r for r in results if r.get("churn_risk") == "high"]
    return jsonify({"results": results, "high_risk_count": len(high_risk)}), 200

def predict_churn_internal(customer):
    prompt = f"Quick churn assessment. Call trend: {customer.get('call_volumes', [])}. Support tickets: {customer.get('support_tickets', 0)}. Last login: {customer.get('last_login_days', 0)} days ago. Return JSON: churn_risk (high/medium/low), probability (float), top_factor (string)."
    result = call_inference([{"role": "system", "content": "Churn analyst."}, {"role": "user", "content": prompt}], max_tokens=100)
    return json.loads(result)

@app.route("/predictions", methods=["GET"])
def list_predictions():
    risk = request.args.get("risk")
    results = predictions[-50:]
    if risk: results = [p for p in results if p.get("churn_risk") == risk]
    return jsonify({"predictions": results}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "predictions": len(predictions)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
