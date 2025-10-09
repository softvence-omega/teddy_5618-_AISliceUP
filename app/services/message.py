import os
import asyncio
import requests
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv
from app.core.config import API_BASE_URL

load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

API_URL = f"{API_BASE_URL}/groupTransaction/getGroups/{{}}"
def fetch_group_data(user_id):
    response = requests.get(API_URL.format(user_id))
    response.raise_for_status()
    return response.json()["data"]

def generate_llm_summary(user_id):
    groups = fetch_group_data(user_id)
    summary_messages = []

    for group in groups:
        group_name = group["groupName"]
        members = group["groupMembers"] + [group["ownerEmail"]]
        
        balances = defaultdict(float)
        for expense in group.get("groupExpenses", []):
            paid_by = expense["paidBy"]["memberEmail"]
            amount = expense["paidBy"]["amount"]
            share_members = expense["shareWith"]["members"]
            share_count = len(share_members)
            share_amount = amount / share_count if share_count else 0

            for member in share_members:
                balances[member] -= share_amount
            balances[paid_by] += amount

        balance_info = ", ".join([f"{m}: {b:.2f}" for m, b in balances.items()])

        system_prompt = (
            "You are Teddy, a friendly and concise finance assistant.\n"
            "Your task:\n"
            "- Receive group expense data (group name, owner, members, all expenses: paidBy, amount, shared members).\n"
            "- Calculate balances for each member.\n"
            "- Generate a short 2-3 line human-readable summary:\n"
            "  - Who owes whom and how much\n"
            "  - Who should receive money\n"
            "  - Who is settled\n"
            "  - Include expense notes in one line\n"
            "Style:\n"
            "- Polite, professional, and friendly\n"
            "- Bullet points optional, keep it compact\n"
            "Example output:\n"
            "💰 Cox's Tour: Rezwan owes Shakila $120, Rezwan is settled. Note: Dinner at Italian restaurant."
        )

        full_prompt = (
            f"Group '{group_name}' balances: {balance_info}. "
            f"Members: {', '.join(members)}. "
            "Extract member names from email addresses. "
            "Generate a short, 2-3 line human-readable summary of who owes whom, "
            "who should receive money, and who is settled. Include notes in one line."
        )

        # Use acreate for async call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )

        summary = response.choices[0].message.content.strip()
        summary_messages.append(f"Group '{group_name}': {summary}")

    return summary_messages
